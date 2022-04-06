import argparse

from debian_cloud_images.api.cdo.upload import Upload
from debian_cloud_images.api.wellknown import label_ucdo_type
from debian_cloud_images.images.azure_computeimage.s1_image import ImagesAzureComputeimageImage
from debian_cloud_images.images.azure_storage.s1_folder import ImagesAzureStorageFolder
from debian_cloud_images.images.azure_storage.s2_blob import ImagesAzureStorageBlob
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver

from .upload_base import UploadBaseCommand


class UploadAzureCommand(UploadBaseCommand):
    argparser_name = 'upload-azure'
    argparser_help = 'upload Debian images to Azure Compute'
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
            '--wait',
            default=True,
            help='wait for long running operation',
            action=argparse.BooleanOptionalAction,
        )

    def __init__(
            self,
            *,
            wait: bool,
            **kw,
    ) -> None:
        super().__init__(**kw)

        self._wait = wait

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._computeimage_tenant = str(self.config_get('azure.image.tenant'))
        self._computeimage_subscription = str(self.config_get('azure.image.subscription'))
        self._computeimage_group = self.config_get('azure.image.group')

        self._storage_tenant = str(self.config_get('azure.storage.tenant'))
        self._storage_subscription = str(self.config_get('azure.storage.subscription'))
        self._storage_group = self.config_get('azure.storage.group')
        self._storage_name = self.config_get('azure.storage.name')
        self._storage_folder = 'vhds'

        if len(self.images) > 1:
            raise RuntimeError('Can only handle one image at a time')

    def __call__(self):
        computeimage_conn = AzureGenericOAuth2Connection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._computeimage_tenant,
            subscription_id=self._computeimage_subscription,
            host='management.azure.com',
            login_resource='https://management.core.windows.net/',
        )
        storage_driver = AzureResourceManagementStorageDriver(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._storage_tenant,
            subscription_id=self._storage_subscription,
        )
        storage_obj = storage_driver.get_storage(
            self._storage_name,
            self._storage_group,
        )
        location = storage_obj.extra['location']

        image_folder = ImagesAzureStorageFolder(
            self._storage_group,
            self._storage_name,
            self._storage_folder,
            storage_driver,
            storage_obj,
        )
        image_folder.create()

        for image in self.images.values():
            try:
                image_public_info = self.image_public_info.apply(image.build_info)
                image_blob_name = f'{image_public_info.vendor_name}.vhd'
                image_blob = ImagesAzureStorageBlob(
                    self._storage_group,
                    self._storage_name,
                    self._storage_folder,
                    image_blob_name,
                    storage_driver,
                    storage_obj,
                )

                print('Uploading image')

                with image.open_image('vhd') as f:
                    image_blob.put(f)

                computeimage_images = []

                for generation in (1, 2):
                    computeimage_image_name = image_public_info.vendor_name_extra(f'g{generation}')

                    computeimage_image = ImagesAzureComputeimageImage(
                        self._computeimage_group,
                        computeimage_image_name,
                        computeimage_conn,
                    )
                    computeimage_images.append(computeimage_image)

                    print(f'Creating image: {computeimage_image_name}')

                    computeimage_image.create(location, {
                        'hyperVGeneration': f'V{generation}',
                        'storageProfile': {
                            'osDisk': {
                                'osType': 'Linux',
                                'blobUri': image_blob.url,
                                'osState': 'Generalized',
                            },
                        },
                    }, wait=False)

                if self._wait:
                    for computeimage_image in computeimage_images:
                        computeimage_image.wait_create()

                metadata = image.build.metadata.copy()
                metadata.labels[label_ucdo_type] = image_public_info.public_type.name

                manifests = [Upload(
                    metadata=metadata,
                    provider=computeimage_conn.connection.host,
                    ref=i.path,
                ) for i in computeimage_images]

                image.write_manifests('upload-azure', manifests, output=self.output)

                for computeimage_image in computeimage_images:
                    print(f'Created image successfully: {computeimage_image.path}')

                # Blob is read in the background, so can't delete if we don't wait
                if self._wait:
                    image_blob.delete()
                else:
                    print('Not deleting blob')

            except BaseException:
                image_blob.delete()
                raise


if __name__ == '__main__':
    UploadAzureCommand._main()
