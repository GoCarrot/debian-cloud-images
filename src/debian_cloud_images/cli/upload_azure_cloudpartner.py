import hashlib
import hmac
import http.client
import logging

from base64 import b64encode, b64decode
from libcloud.common.exceptions import BaseHTTPError
from libcloud.storage.drivers.azure_blobs import AzureBlobLease
from urllib.parse import urlsplit, urlunsplit, urlencode

from .upload_base import UploadBaseCommand
from ..api.cdo.upload import Upload
from ..api.wellknown import label_ucdo_provider, label_ucdo_type
from ..utils import argparse_ext
from ..utils.files import ChunkedFile
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection
from ..utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver


class AzureCloudPartnerOffer:
    def __init__(self, driver, publisher_id, offer_id):
        self.driver = driver
        self.publisher_id = publisher_id
        self.offer_id = offer_id

        self.offer_path = '/api/publishers/{}/offers/{}'.format(publisher_id, offer_id)

        self.read()

    def _request(self, params=None, headers=None, data=None, method='GET'):
        return self.driver.request(self.offer_path, headers=headers, params=params, data=data, method=method)

    def publish(self, email):
        data = {
            'metadata': {
                'notification-emails': email,
            },
        }
        try:
            self.driver.request(self.offer_path + '/publish', data=data, method='POST')
        except BaseHTTPError as e:
            logging.error(f'Unable to publish offer: {e.message}')

    def read(self):
        r = self._request()
        self.data, self.etag = r.parse_body(), r.headers['etag']
        self.plans = {i['planId']: i for i in self.data['definition']['plans']}

    def save(self):
        r = self._request(data=self.data, method='PUT', headers={'If-Match': self.etag})
        return r.parse_body()


class UploadOffer(AzureCloudPartnerOffer):
    def __init__(self, *args):
        super().__init__(*args)
        self.images = []

    def check_image(self, image):
        if image.build_vendor != 'azure':
            logging.warning('Image %s is no Azure image, ignoring', image.name)
            return

        azure_version = image.build_info['version_azure']
        release_id = image.build_release_id

        plan = self.plans.get(release_id, None)

        if not plan:
            logging.warning('Release %s does not exist', release_id)
            return

        plan_images = plan['microsoft-azure-corevm.vmImagesPublicAzure']

        if azure_version in plan_images:
            logging.warning('Image %s (%s) already exists for release %s', image.name, azure_version, release_id)
            return

        self.images.append(image)


class UrlSas:
    """ URL for Azure storage with shared access signature (only supported for container) """
    def __init__(self, url, storage_secret, *, sas_permission='r', sas_start=None, sas_expiry=None):
        url = urlsplit(url, scheme='https', allow_fragments=False)
        self._set_scheme(url)
        self._set_netloc(url)
        self._set_path(url)

        self._storage_secret = storage_secret
        self._sas_permission = sas_permission.encode('ascii')
        self._sas_start = sas_start.encode('ascii')
        self._sas_expiry = sas_expiry.encode('ascii')

    def _set_scheme(self, url):
        assert url.scheme
        self.scheme = url.scheme

    def _set_netloc(self, url):
        assert url.netloc
        self.netloc = url.netloc
        if url.netloc.endswith('.blob.core.windows.net'):
            self._account = url.netloc.split('.', 1)[0].encode('ascii')

    def _set_path(self, url):
        assert url.path
        self.path = url.path
        path = url.path.split('/', 2)
        assert path[0] == ''
        self._container = path[1].encode('ascii')
        self._file = path[2]

    def __iter__(self):
        yield self.scheme
        yield self.netloc
        yield self.path
        yield self.query
        yield self.fragment

    def __str__(self):
        return urlunsplit(self)

    @property
    def query(self):
        query = {
            'sr': 'c',
        }
        tosign = []

        def add(p, value=None):
            if value is not None:
                query[p] = value
                tosign.append(value)
            else:
                tosign.append('')

        add('sp', self._sas_permission)
        add('st', self._sas_start)
        add('se', self._sas_expiry)
        tosign.append(b'/blob/' + self._account + b'/' + self._container)
        tosign.append(b'')  # SIGNED_IDENTIFIER
        tosign.append(b'')  # SIGNED_IP
        tosign.append(b'')  # SIGNED_PROTOCOL
        add('sv', b'2018-03-28')
        tosign.append(b'')  # SIGNED_CACHE_CONTROL
        tosign.append(b'')  # SIGNED_CONTENT_DISPOSITION
        tosign.append(b'')  # SIGNED_CONTENT_ENCODING
        tosign.append(b'')  # SIGNED_CONTENT_LANGUAGE
        tosign.append(b'')  # SIGNED_CONTENT_TYPE

        key = b64decode(self._storage_secret)
        signed_hmac_sha256 = hmac.HMAC(key, b'\n'.join(tosign), hashlib.sha256)
        query['sig'] = b64encode(signed_hmac_sha256.digest())

        return urlencode(query)

    @property
    def fragment(self):
        return None


class ImageUploaderAzureCloudpartner:
    def __init__(self, output, publisher_id, storage_id, auth, publish):
        self.output = output
        self.publisher_id = publisher_id
        self.storage_id = storage_id
        self.auth = auth
        self.publish = publish

        self.__cloudpartner = self.__storage = self.__storage_driver = self.__storage_secret = None

    @property
    def cloudpartner(self):
        ret = self.__cloudpartner
        if ret is None:
            ret = AzureCloudpartnerOAuth2Connection(
                tenant_id=self.auth.tenant_id,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
            ret.connect()
            self.__cloudpartner = ret
        return ret

    @property
    def storage(self):
        ret = self.__storage
        if ret is None:
            ret = self.__storage = self.storage_driver.get_storage(
                self.storage_id,
            )
        return ret

    @property
    def storage_driver(self):
        ret = self.__storage_driver
        if ret is None:
            ret = self.__storage_driver = AzureResourceManagementStorageDriver(
                tenant_id=self.auth.tenant_id,
                subscription_id=None,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
        return ret

    @property
    def storage_secret(self):
        ret = self.__storage_secret
        if ret is None:
            ret = self.__storage_secret = self.storage_driver.get_storagekeys(
                self.storage_id,
            )[0]
        return ret

    def __call__(self, images, image_public_info):
        for offer in self.filter_images(images.values(), image_public_info).values():
            changed = False

            for image in offer.images:
                image_name = image_public_info.apply(image.build_info).vendor_name
                image_file = '{}/disk.vhd'.format(image_name)
                image_url = 'https://{}/{}'.format(self.storage.connection.host, image_file)
                image_url_sas = UrlSas(
                    image_url,
                    self.storage_secret,
                    sas_permission='rl',
                    sas_start='2018-01-01T00:00:00Z',
                    sas_expiry='2020-01-01T00:00:00Z',
                )

                logging.info('Uploading image %s to %s/%s', image.name, offer.publisher_id, offer.offer_id)

                self.create_container(image_name)
                self.upload_file(image, image_file)

                if self.insert_image(offer, image, image_public_info, image_url_sas):
                    changed = True

                    azure_version = image.build_info['version_azure']
                    ref = f'{offer.publisher_id}:{offer.offer_id}:{image.build_release_id}:{azure_version}'
                    family_ref = f'{offer.publisher_id}:{offer.offer_id}:{image.build_release_id}:latest'

                    metadata = image.build.metadata.copy()
                    metadata.labels[label_ucdo_provider] = 'azure.com'
                    metadata.labels[label_ucdo_type] = image_public_info.public_type.name

                    manifests = [Upload(
                        metadata=metadata,
                        provider=self.cloudpartner.host,
                        ref=ref,
                        family_ref=family_ref,
                    )]

                    image.write_manifests('upload-azure-cloudpartner', manifests, output=self.output)

            if changed and self.publish:
                logging.info('Publishing offer %s', offer.offer_id)
                offer.publish(self.publish)

    def create_container(self, container):
        logging.info('Creating container %s', container)

        r = self.storage.connection.request(
            container,
            method='PUT',
            params={
                'restype': 'container',
            },
        )
        if r.status != http.client.CREATED:
            raise RuntimeError('Error creating container: {0.error} ({0.status})'.format(r))

    def upload_file(self, image, path):
        """ Upload file to Storage """
        logging.info('Uploading file to %s', path)

        with image.open_image('vhd') as f:
            chunked = ChunkedFile(f, 4 * 1024 * 1024)

            with AzureBlobLease(self.storage, path, True) as lease:
                headers = {
                    'x-ms-blob-type': 'PageBlob',
                    'x-ms-blob-content-length': str(chunked.size),
                }
                lease.update_headers(headers)

                r = self.storage.connection.request(
                    path,
                    method='PUT',
                    headers=headers,
                )
                if r.status != http.client.CREATED:
                    raise RuntimeError('Error creating file: {0.error} ({0.status})'.format(r))

                for chunk in chunked:
                    self.upload_file_chunk(path, lease, chunk)

    def upload_file_chunk(self, path, lease, chunk):
        """ Upload a single block up to 4MB to Azure storage """
        buf = chunk.read()
        logging.debug('uploading start=%s, size=%s', chunk.offset, chunk.size)

        headers = {
            'Content-Length': chunk.size,
            'Range': 'bytes={}-{}'.format(chunk.offset, chunk.offset + chunk.size - 1),
            'x-ms-page-write': 'update',
        }
        lease.update_headers(headers)
        lease.renew()

        r = self.storage.connection.request(
            path,
            method='PUT',
            params={
                'comp': 'page',
            },
            headers=headers,
            data=buf,
        )
        if r.status != http.client.CREATED:
            raise RuntimeError('Error uploading file block: {0.error} ({0.status})'.format(r))

    def filter_images(self, images, image_public_info):
        offers = {}

        for image in images:
            image_info = image_public_info.apply(image.build_info)
            offer_id = image_info.azure_offer
            if offer_id not in offers:
                offer = offers.setdefault(offer_id, UploadOffer(self.cloudpartner, self.publisher_id, offer_id))
            else:
                offer = offers[offer_id]
            offer.check_image(image)

        return offers

    def insert_image(self, offer, image, image_public_info, image_url_sas):
        image_name = image_public_info.apply(image.build_info).vendor_name
        image_family = image_public_info.apply(image.build_info).vendor_azure_family
        image_description = image_public_info.apply(image.build_info).vendor_description

        azure_version = image.build_info['version_azure']
        release_id = image.build_release_id

        offer.read()
        plan = offer.plans[release_id]
        plan_images = plan['microsoft-azure-corevm.vmImagesPublicAzure']
        if azure_version in plan_images:
            raise RuntimeError('Image %s already exists', image.name)

        logging.info('Inserting image %s (%s) for release %s', image.name, azure_version, release_id)
        plan_images[azure_version] = {
            'description': image_description,
            'label': image_family,
            'mediaName': image_name,
            'osVhdUrl': str(image_url_sas),
        }

        for generation in plan.get('diskGenerations', []):
            generation_id = generation['planId']
            logging.info('Inserting image %s (%s) for release %s generation %s', image.name, azure_version, release_id, generation_id)
            generation_images = generation['microsoft-azure-corevm.vmImagesPublicAzure']
            generation_images[azure_version] = {
                'description': image_description,
                'label': image_family,
                'mediaName': f'{image_name}-{generation_id}',
                'osVhdUrl': str(image_url_sas),
            }

        logging.info('Saving offer %s/%s', offer.publisher_id, offer.offer_id)
        offer.save()
        return True


class UploadAzureCloudpartnerCommand(UploadBaseCommand):
    argparser_name = 'upload-azure-cloudpartner'
    argparser_help = 'upload Debian images for publishing via Azure Cloud Partner interface'

    @classmethod
    def _argparse_register(cls, parser, config):
        super()._argparse_register(parser, config)

        parser.add_argument(
            '--publisher',
            action=argparse_ext.ConfigStoreAction,
            config=config,
            config_key='azure-publisher',
            dest='publisher_id',
            help='Azure publisher',
            metavar='PUBLISHER',
            required=True,
        )
        parser.add_argument(
            '--storage',
            action=argparse_ext.ConfigStoreAction,
            config=config,
            config_key='azure-storage',
            dest='storage_id',
            help='Name or ID of Azure storage',
            metavar='ID',
            required=True,
        )
        parser.add_argument(
            '--auth',
            action=argparse_ext.ConfigStoreAzureAuthAction,
            config=config,
            required=True,
        )
        parser.add_argument(
            '--publish',
            help='Publish and set notification email',
            metavar='EMAIL',
        )

    def __init__(
            self, *,
            publisher_id,
            storage_id,
            auth=None,
            publish=None,
            **kw,
    ):
        super().__init__(**kw)

        self.uploader = ImageUploaderAzureCloudpartner(
            output=self.output,
            publisher_id=publisher_id,
            storage_id=storage_id,
            auth=auth,
            publish=publish,
        )

    def __call__(self):
        self.uploader(self.images, self.image_public_info)


if __name__ == '__main__':
    UploadAzureCloudpartnerCommand._main()
