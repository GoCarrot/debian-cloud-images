import argparse
import hashlib
import hmac
import http.client
import logging

from base64 import b64encode, b64decode
from libcloud.storage.drivers.azure_blobs import AzureBlobLease
from libcloud.storage.providers import get_driver as storage_driver
from libcloud.storage.types import Provider as StorageProvider
from urllib.parse import urlsplit, urlunsplit, urlencode

from .upload_base import UploadBaseCommand
from ..utils.files import ChunkedFile
from ..utils.libcloud.storage.azure_blobs import AzureGenericOAuth2Connection


class AzureAuth:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret


class ActionAzureAuth(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, AzureAuth(*value.split(':')))


class AzureCloudpartnerOAuth2Connection(AzureGenericOAuth2Connection):
    """ OAuth 2 authenticated connection for Azure Cloud Partner interface """
    def __init__(self, *, tenant_id, client_id, client_secret):
        super().__init__(
            host='cloudpartner.azure.com',
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            login_host='login.microsoftonline.com',
            login_resource='https://cloudpartner.azure.com',
        )

    def add_default_params(self, params):
        params.update({
            'api-version': '2017-10-31',
        })
        return params


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
    storage_cls = storage_driver(StorageProvider.AZURE_BLOBS)

    def __init__(self, publisher_id, offer_id, storage_name, storage_container, storage_secret, auth, publish):
        self.publisher_id = publisher_id
        self.offer_id = offer_id
        self.storage_name = storage_name
        self.storage_container = storage_container
        self.storage_secret = storage_secret
        self.auth = auth
        self.publish = publish

        self.__cloudpartner = self.__storage = None

        self.offer = '/api/publishers/{}/offers/{}'.format(publisher_id, offer_id)

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
            ret = self.__storage = self.storage_cls(
                key=self.storage_name,
                secret=self.storage_secret,
            )
        return ret

    def __call__(self, images, image_public_info):
        offer, etag = self.read_offer()
        definition = offer['definition']
        plans = {i['planId']: i for i in definition['plans']}
        changed = False

        for image in images.values():
            try:
                image_name = image_public_info.apply(image.build_info).vendor_name
                image_description = image_public_info.apply(image.build_info).vendor_description
                image_path = '/{}/{}.vhd'.format(self.storage_container, image_name)
                image_url_sas = UrlSas(
                    'https://{}.blob.core.windows.net{}'.format(self.storage_name, image_path),
                    self.storage_secret,
                    sas_permission='rl',
                    sas_start='2018-01-01T00:00:00Z',
                    sas_expiry='2020-01-01T00:00:00Z',
                )

                self.upload_file(image, image_path)

                changed |= self.insert_image(plans, image, image_name, image_description, image_url_sas)

            except Exception:
                logging.exception('Failed to insert image')

        if changed:
            logging.info('Saving offer %s/%s', self.publisher_id, self.offer_id)
            self.save_offer(offer, etag)

            if self.publish:
                logging.info('Publishing offer %s', self.offer_id)
                self.publish_offer(self.publish)
        else:
            logging.info('Neither saving nor publishing unchanged offer %s/%s', self.publisher_id, self.offer_id)

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

    def _offer(self, params=None, headers=None, data=None, method='GET'):
        return self.cloudpartner.request(self.offer, headers=headers, params=params, data=data, method=method)

    def read_offer(self):
        r = self._offer()
        return r.parse_body(), r.headers['etag']

    def publish_offer(self, email):
        data = {
            'metadata': {
                'notification-emails': email,
            },
        }
        self.cloudpartner.request(self.offer + '/publish', data=data, method='POST')

    def save_offer(self, data, etag):
        r = self._offer(data=data, method='PUT', headers={'If-Match': etag})
        return r.parse_body()

    def insert_image(self, plans, image, image_name, image_description, image_url_sas):
        azure_version = image.build_info['version_azure']
        release_id = image.build_release_id

        plan = plans[release_id]
        plan_images = plan['microsoft-azure-corevm.vmImagesPublicAzure']
        if azure_version in plan_images:
            logging.warning('Image %s (%s) already exists for release %s', image_name, azure_version, release_id)
            return False

        else:
            logging.info('Inserting image %s (%s) for release %s', image_name, azure_version, release_id)
            plan_images[azure_version] = {
                'description': image_description,
                'label': image_name,
                'mediaName': image_name,
                'osVhdUrl': str(image_url_sas),
            }
            return True


class UploadAzureCloudpartnerCommand(UploadBaseCommand):
    argparser_name = 'upload-azure-cloudpartner'
    argparser_help = 'upload Debian images for publishing via Azure Cloud Partner interface'
    argparser_usage = '%(prog)s PUBLISHER OFFER STORAGE_NAME STORAGE_CONTAINER STORAGE_SECRET'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            'publisher_id',
            help='Azure publisher',
            metavar='PUBLISHER',
        )
        parser.add_argument(
            'offer_id',
            help='Azure offer',
            metavar='OFFER',
        )
        parser.add_argument(
            'storage_name',
            help='Azure Storage name',
            metavar='STORAGE_NAME',
        )
        parser.add_argument(
            'storage_container',
            help='Azure Storage container',
            metavar='STORAGE_CONTAINER',
        )
        parser.add_argument(
            'storage_secret',
            help='Azure Storage access key',
            metavar='STORAGE_SECRET',
        )

        parser.add_argument(
            '--auth',
            action=ActionAzureAuth,
            help='Authentication info for Azure AD application',
            metavar='TENANT:APPLICATION:SECRET',
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
            offer_id,
            storage_name,
            storage_container,
            storage_secret,
            auth=None,
            publish=None,
            **kw,
    ):
        super().__init__(**kw)

        self.uploader = ImageUploaderAzureCloudpartner(
            publisher_id=publisher_id,
            offer_id=offer_id,
            storage_name=storage_name,
            storage_container=storage_container,
            storage_secret=storage_secret,
            auth=auth,
            publish=publish,
        )

    def __call__(self):
        self.uploader(self.images, self.image_public_info)


if __name__ == '__main__':
    parser = UploadAzureCloudpartnerCommand._argparse_init_base()
    args = parser.parse_args()
    UploadAzureCloudpartnerCommand(**vars(args))()