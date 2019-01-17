import argparse
import http.client
import logging

from .upload_base import UploadBaseCommand
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

    def __init__(self, storage_group, storage_name, storage_container, image_group, auth, variant, version_override):
        self.storage_group = storage_group
        self.storage_name = storage_name
        self.storage_container = storage_container
        self.image_group = image_group
        self.auth = auth
        self.variant = variant
        self.version_override = version_override

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

    def __call__(self, image):
        if image.build_vendor != 'azure':
            logging.warning('Image %s is no Azure image, ignoring', image.name)
            return

        image_name = image.image_name(self.variant, self.version_override)
        image_path = '/{}/{}.vhd'.format(self.storage_container, image_name)
        image_url = 'https://{}.blob.core.windows.net{}'.format(self.storage_name, image_path)

        self.upload_file(image, image_path)
        self.create_image(image, image_name, image_url)

        image.write_vendor_manifest(
            'upload_vendor',
            {
            },
        )

        self.delete_file(image, image_path)

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

    def delete_file(self, image, path):
        logging.info('Deleting file %ss', path)

        self.storage.connection.request(
            path,
            method='DELETE',
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
    argparser_usage = '%(prog)s STORAGE CONTAINER'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            'group',
            action=ActionAzureResourceGroup,
            help='Azure Subscription and Resource group',
            metavar='SUBSCRIPTION:GROUP',
        )
        parser.add_argument(
            'storage_name',
            help='Azure Storage name',
            metavar='STORAGE',
        )
        parser.add_argument(
            'storage_container',
            help='Azure Storage container',
            metavar='CONTAINER',
        )
        parser.add_argument(
            '--auth',
            action=ActionAzureAuth,
            help='Authentication info for Azure AD application',
            metavar='TENANT:APPLICATION:SECRET',
        )

    def __init__(self, *, group=None, storage_name=None, storage_container=None, auth=None, variant=None, version_override=None, **kw):
        super().__init__(**kw)

        self.uploader = ImageUploaderAzure(
            storage_group=group,
            storage_name=storage_name,
            storage_container=storage_container,
            image_group=group,
            auth=auth,
            variant=variant,
            version_override=version_override,
        )


if __name__ == '__main__':
    parser = UploadAzureCommand._argparse_init_base()
    args = parser.parse_args()
    UploadAzureCommand(**vars(args))()
