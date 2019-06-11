import argparse
import http.client
import logging

from .upload_base import UploadBaseCommand
from ..api.cdo.upload import Upload
from ..api.wellknown import label_ucdo_type
from ..utils.files import ChunkedFile
from ..utils.libcloud.compute.azure_arm import ExAzureNodeDriver
from ..utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver
from ..utils.libcloud.storage.azure_blobs import AzureBlobsOAuth2StorageDriver

from libcloud.storage.types import Provider as StorageProvider
from libcloud.storage.providers import get_driver as storage_driver
from libcloud.storage.drivers.azure_blobs import AzureBlobLease


class AzureAuth:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret


class AzureResourceGroup:
    def __init__(self, subscription_id, resource_group):
        self.subscription_id = subscription_id
        self.resource_group = resource_group


class ActionAzureAuth(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, AzureAuth(*value.split(':')))


class ActionAzureResourceGroup(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, AzureResourceGroup(*value.split(':')))


class ImageUploaderAzure:
    storage_cls = storage_driver(StorageProvider.AZURE_BLOBS)

    def __init__(self, storage_group, storage_name, image_group, auth):
        self.storage_group = storage_group
        self.storage_name = storage_name
        self.image_group = image_group
        self.auth = auth

        self.__compute_driver = self.__storage = self.__storage_driver = None

    @property
    def compute_driver(self):
        ret = self.__compute_driver
        if ret is None:
            ret = self.__compute_driver = ExAzureNodeDriver(
                tenant_id=self.auth.tenant_id,
                subscription_id=self.storage_group.subscription_id,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
        return ret

    @property
    def storage(self):
        ret = self.__storage
        if ret is None:
            ret = self.__storage = AzureBlobsOAuth2StorageDriver(
                key=self.storage_name,
                tenant_id=self.auth.tenant_id,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
        return ret

    @property
    def storage_driver(self):
        ret = self.__storage_driver
        if ret is None:
            ret = self.__storage_driver = AzureResourceManagementStorageDriver(
                tenant_id=self.auth.tenant_id,
                subscription_id=self.storage_group.subscription_id,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
        return ret

    def __call__(self, image, public_info):
        if image.build_vendor != 'azure':
            logging.warning('Image %s is no Azure image, ignoring', image.name)
            return

        image_name = public_info.vendor_name
        image_file = '{}/disk.vhd'.format(image_name)
        image_url = 'https://{}.blob.core.windows.net/{}'.format(self.storage_name, image_file)

        self.create_container(image_name)
        self.upload_file(image, image_file)
        image_id = self.create_image(image, image_name, image_url)

        metadata = image.build.metadata.copy()
        metadata.labels[label_ucdo_type] = public_info.public_type.name

        manifests = [Upload(
            metadata=metadata,
            provider=self.compute_driver.connection.host,
            ref=image_id,
        )]

        image.write_manifests('upload-azure', manifests)

        self.delete_container(image_name)

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

    def create_image(self, image, image_name, image_url):
        image_storage = self.storage_driver.get_storage(self.storage_group.resource_group, self.storage_name)
        image_location = image_storage.extra['location']

        logging.info('Create image %s/%s in %s', self.image_group.resource_group, image_name, image_location)

        return self.compute_driver.ex_create_computeimage(
            name=image_name,
            ex_resource_group=self.image_group.resource_group,
            location=image_location,
            ex_blob=image_url,
        )

    def delete_container(self, container):
        logging.info('Deleting container %s', container)

        self.storage.connection.request(
            container,
            method='DELETE',
            params={
                'restype': 'container',
            },
        )

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


class UploadAzureCommand(UploadBaseCommand):
    argparser_name = 'upload-azure'
    argparser_help = 'upload Debian images to Azure'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--group',
            action=ActionAzureResourceGroup,
            help='Azure Subscription and Resource group',
            metavar='SUBSCRIPTION:GROUP',
            required=True,
        )
        parser.add_argument(
            '--storage-name',
            help='Azure Storage name',
            metavar='STORAGE',
            required=True,
        )
        parser.add_argument(
            '--auth',
            action=ActionAzureAuth,
            help='Authentication info for Azure AD application',
            metavar='TENANT:APPLICATION:SECRET',
            required=True,
        )

    def __init__(self, *, group=None, storage_name=None, auth=None, **kw):
        super().__init__(**kw)

        self.uploader = ImageUploaderAzure(
            storage_group=group,
            storage_name=storage_name,
            image_group=group,
            auth=auth,
        )


if __name__ == '__main__':
    parser = UploadAzureCommand._argparse_init_base()
    args = parser.parse_args()
    UploadAzureCommand(**vars(args))()
