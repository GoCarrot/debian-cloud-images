import http.client
import logging

from collections import namedtuple
from libcloud.storage.drivers.azure_blobs import AzureBlobLease

from .upload_base import UploadBaseCommand
from ..api.cdo.upload import Upload
from ..api.wellknown import label_ucdo_type
from ..utils.files import ChunkedFile
from ..utils.libcloud.compute.azure_arm import ExAzureNodeDriver
from ..utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver


AzureAuth = namedtuple('AzureAuth', ('client', 'secret'))
AzureImage = namedtuple('AzureImage', ('tenant', 'subscription', 'group'))
AzureStorage = namedtuple('AzureStorage', ('tenant', 'subscription', 'group', 'name'))


class ImageUploaderAzure:
    def __init__(self, output, image, storage, generation, auth):
        self.output = output
        self.image = image
        self.storage = storage
        self.generation = generation
        self.auth = auth

        self.__image_driver = self.__storage_obj = self.__storage_driver = None

    @property
    def image_driver(self):
        ret = self.__image_driver
        if ret is None:
            ret = self.__image_driver = ExAzureNodeDriver(
                tenant_id=self.image.tenant,
                subscription_id=self.image.subscription,
                client_id=self.auth.client,
                client_secret=self.auth.secret,
            )
        return ret

    @property
    def storage_obj(self):
        ret = self.__storage_obj
        if ret is None:
            ret = self.__storage_obj = self.storage_driver.get_storage(
                name=self.storage.name,
                resource_group=self.storage.group,
            )
        return ret

    @property
    def storage_driver(self):
        ret = self.__storage_driver
        if ret is None:
            ret = self.__storage_driver = AzureResourceManagementStorageDriver(
                tenant_id=self.storage.tenant,
                subscription_id=self.storage.subscription,
                client_id=self.auth.client,
                client_secret=self.auth.secret,
            )
        return ret

    def __call__(self, image, public_info):
        image_name = public_info.vendor_name63
        image_file = '{}/disk.vhd'.format(image_name)
        image_url = 'https://{}/{}'.format(self.storage_obj.connection.host, image_file)

        self.create_container(image_name)
        self.upload_file(image, image_file)
        image_id = self.create_image(image, image_name, image_url)

        metadata = image.build.metadata.copy()
        metadata.labels[label_ucdo_type] = public_info.public_type.name

        manifests = [Upload(
            metadata=metadata,
            provider=self.image_driver.connection.host,
            ref=image_id,
        )]

        image.write_manifests('upload-azure', manifests, output=self.output)

        self.delete_container(image_name)

    def create_container(self, container):
        logging.info('Creating container %s', container)

        r = self.storage_obj.connection.request(
            container,
            method='PUT',
            params={
                'restype': 'container',
            },
        )
        if r.status != http.client.CREATED:
            raise RuntimeError('Error creating container: {0.error} ({0.status})'.format(r))

    def create_image(self, image, image_name, image_url):
        image_location = self.storage_obj.extra['location']

        logging.info('Create image %s/%s in %s', self.image.group, image_name, image_location)

        return self.image_driver.ex_create_computeimage(
            name=image_name,
            ex_resource_group=self.image.group,
            location=image_location,
            ex_blob=image_url,
            ex_generation=self.generation,
        )

    def delete_container(self, container):
        logging.info('Deleting container %s', container)

        self.storage_obj.connection.request(
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

            with AzureBlobLease(self.storage_obj, path, True) as lease:
                headers = {
                    'x-ms-blob-type': 'PageBlob',
                    'x-ms-blob-content-length': str(chunked.size),
                }
                lease.update_headers(headers)

                r = self.storage_obj.connection.request(
                    path,
                    method='PUT',
                    headers=headers,
                )
                if r.status != http.client.CREATED:
                    raise RuntimeError('Error creating file: {0.error} ({0.status})'.format(r))

                for chunk in chunked:
                    if chunk.is_data:
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

        r = self.storage_obj.connection.request(
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
    argparser_epilog = '''
config options:
  azure.auth.client     application ID of service account, or empty for using az
  azure.auth.secret     secret of service account, or empty for using az
  azure.image.tenant
  azure.image.subscription
  azure.image.group
  azure.storage.tenant
  azure.storage.subscription
  azure.storage.group
  azure.storage.name
'''

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--generation',
            choices=(1, 2),
            default=1,
            help='Generation of VM (1 is legacy, 2 is UEFI and modern emulation)',
            type=int,
        )

    def __init__(self, *, generation, **kw):
        super().__init__(**kw)

        auth = AzureAuth(
            client=str(self.config_get('azure.auth.client', default=None)),
            secret=self.config_get('azure.auth.secret', default=None),
        )
        image = AzureImage(
            tenant=str(self.config_get('azure.image.tenant', 'azure.storage.tenant')),
            subscription=str(self.config_get('azure.image.subscription', 'azure.storage.subscription')),
            group=self.config_get('azure.image.group', 'azure.storage.group'),
        )
        storage = AzureStorage(
            tenant=str(self.config_get('azure.storage.tenant')),
            subscription=str(self.config_get('azure.storage.subscription')),
            group=self.config_get('azure.storage.group'),
            name=self.config_get('azure.storage.name'),
        )

        self.uploader = ImageUploaderAzure(
            output=self.output,
            image=image,
            storage=storage,
            generation=generation,
            auth=auth,
        )


if __name__ == '__main__':
    UploadAzureCommand._main()
