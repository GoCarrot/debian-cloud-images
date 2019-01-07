import argparse
import http.client
import logging

from .upload_base import UploadBaseCommand
from ..utils.files import ChunkedFile
from ..utils.libcloud.storage.azure_blobs import AzureBlobsOAuth2StorageDriver

from libcloud.storage.types import Provider as StorageProvider
from libcloud.storage.providers import get_driver as storage_driver
from libcloud.storage.drivers.azure_blobs import AzureBlobLease


class AzureAuth:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret


class ActionAzureAuth(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, AzureAuth(*value.split(':')))


class ImageUploaderAzure:
    storage_cls = storage_driver(StorageProvider.AZURE_BLOBS)

    def __init__(self, storage_name, storage_container, auth, storage_secret, variant, version_override):
        self.storage_name = storage_name
        self.storage_container = storage_container
        self.auth = auth
        self.storage_secret = storage_secret
        self.variant = variant
        self.version_override = version_override

        self.__storage = None

    @property
    def storage(self):
        ret = self.__storage
        if ret is None:
            if self.auth:
                ret = AzureBlobsOAuth2StorageDriver(
                    key=self.storage_name,
                    tenant_id=self.auth.tenant_id,
                    client_id=self.auth.client_id,
                    client_secret=self.auth.client_secret,
                )
            else:
                ret = self.storage_cls(
                    key=self.storage_name,
                    secret=self.storage_secret,
                )
            self.__storage = ret
        return ret

    def __call__(self, image):
        if image.build_vendor != 'azure':
            logging.warning('Image %s is no Azure image, ignoring', image.name)
            return

        image_name = image.image_name(self.variant, self.version_override)
        image_path = '/{}/{}.vhd'.format(self.storage_container, image_name)
        image_url = 'https://{}.blob.core.windows.net{}'.format(self.storage_name, image_path)

        self.upload_file(image, image_path)

        image.write_vendor_manifest(
            'upload_vendor',
            {
                'url': image_url,
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
    argparser_usage = '%(prog)s STORAGE CONTAINER'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

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

        auth_group = parser.add_mutually_exclusive_group(required=True)
        auth_group.add_argument(
            '--auth',
            action=ActionAzureAuth,
            help='Authentication info for Azure AD application',
            metavar='TENANT:APPLICATION:SECRET',
        )
        auth_group.add_argument(
            '--storage-secret',
            help='Azure Storage access key',
            metavar='SECRET',
        )

    def __init__(self, *, storage_name=None, storage_container=None, auth=None, storage_secret=None, variant=None, version_override=None, **kw):
        super().__init__(**kw)

        self.uploader = ImageUploaderAzure(
            storage_name=storage_name,
            storage_container=storage_container,
            auth=auth,
            storage_secret=storage_secret,
            variant=variant,
            version_override=version_override,
        )


if __name__ == '__main__':
    parser = UploadAzureCommand._argparse_init_base()
    args = parser.parse_args()
    UploadAzureCommand(**vars(args))()
