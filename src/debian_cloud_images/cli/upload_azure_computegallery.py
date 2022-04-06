import argparse

from debian_cloud_images.api.cdo.upload import Upload
from debian_cloud_images.api.wellknown import label_ucdo_type
from debian_cloud_images.images.azure_computegallery.s2_version import ImagesAzureComputegalleryVersion
from debian_cloud_images.images.azure_storage.s1_folder import ImagesAzureStorageFolder
from debian_cloud_images.images.azure_storage.s2_blob import ImagesAzureStorageBlob
from debian_cloud_images.utils.azure.image_version import AzureImageVersion
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver

from .upload_base import UploadBaseCommand


class UploadAzureComputegalleryCommand(UploadBaseCommand):
    argparser_name = 'upload-azure-computegallery'
    argparser_help = 'upload Debian images to Azure Compute Gallery'
    argparser_epilog = '''
config options:
  azure.auth.client     application ID of service account, or empty for using az
  azure.auth.secret     secret of service account, or empty for using az
  azure.computegallery.tenant
  azure.computegallery.subscription
  azure.computegallery.group
  azure.computegallery.name
  azure.storage.tenant
  azure.storage.subscription
  azure.storage.group
  azure.storage.name
'''

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--computegallery-image',
            help='use specified image inside Azure Compute Gallery',
            metavar='IMAGE',
            required=True,
        )
        parser.add_argument(
            '--computegallery-version-override',
            help='use specified image version inside Azure Compute Gallery',
            metavar='VERSION',
            type=AzureImageVersion.from_string,
        )
        parser.add_argument(
            '--wait',
            default=True,
            help='wait for long running operation',
            action=argparse.BooleanOptionalAction,
        )

    def __init__(
            self, *,
            computegallery_image: str,
            computegallery_version_override: AzureImageVersion,
            wait: bool,
            **kw,
    ):
        super().__init__(**kw)

        self._computegallery_image = computegallery_image
        self._computegallery_version_override = computegallery_version_override
        self._storage_folder = computegallery_image
        self._wait = wait

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._computegallery_tenant = str(self.config_get('azure.computegallery.tenant'))
        self._computegallery_subscription = str(self.config_get('azure.computegallery.subscription'))
        self._computegallery_group = self.config_get('azure.computegallery.group')
        self._computegallery_name = self.config_get('azure.computegallery.name')

        self._storage_tenant = str(self.config_get('azure.storage.tenant'))
        self._storage_subscription = str(self.config_get('azure.storage.subscription'))
        self._storage_group = self.config_get('azure.storage.group')
        self._storage_name = self.config_get('azure.storage.name')

        if len(self.images) > 1:
            raise RuntimeError('Can only handle one image at a time')

    def __call__(self):
        computegallery_conn = AzureGenericOAuth2Connection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._computegallery_tenant,
            subscription_id=self._computegallery_subscription,
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
                if self._computegallery_version_override is not None:
                    image_version = self._computegallery_version_override
                elif 'version_azure' in image.build_info:
                    image_version = image.build_info['version_azure']
                else:
                    raise RuntimeError('No Azure version, use --computegallery-version-override')

                image_blob_name = f'{image_version}.vhd'
                image_blob = ImagesAzureStorageBlob(
                    self._storage_group,
                    self._storage_name,
                    self._storage_folder,
                    image_blob_name,
                    storage_driver,
                    storage_obj,
                )

                computegallery_version = ImagesAzureComputegalleryVersion(
                    self._computegallery_group,
                    self._computegallery_name,
                    self._computegallery_image,
                    image_version,
                    computegallery_conn,
                )

                print(f'Uploading image version: {image_version}')

                with image.open_image('vhd') as f:
                    image_blob.put(f)

                print(f'Creating image version: {image_version}')

                computegallery_version.create(location, {
                    'storageProfile': {
                        'osDiskImage': {
                            'source': {
                                'id': f'/subscriptions/{self._storage_subscription}/resourceGroups/{self._storage_group}/providers/Microsoft.Storage/storageAccounts/{self._storage_name}',
                                'uri': image_blob.url,
                            }
                        }
                    }
                }, wait=self._wait)

                metadata = image.build.metadata.copy()
                metadata.labels[label_ucdo_type] = self.image_public_info.apply(image.build_info).public_type.name

                manifests = [Upload(
                    metadata=metadata,
                    provider=computegallery_conn.connection.host,
                    family_ref=computegallery_version.path.rsplit('/', 2)[0],
                    ref=computegallery_version.path,
                )]

                image.write_manifests('upload-azure-computegallery', manifests, output=self.output)

                print(f'Created image version successfully: {computegallery_version.path}')

                # Blob is read in the background, so can't delete if we don't wait
                if self._wait:
                    image_blob.delete()
                else:
                    print('Not deleting blob')

            except BaseException:
                image_blob.delete()
                raise


if __name__ == '__main__':
    UploadAzureComputegalleryCommand._main()
