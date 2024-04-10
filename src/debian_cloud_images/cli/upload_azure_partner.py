# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import pathlib

from debian_cloud_images.api.cdo.upload import Upload
from debian_cloud_images.api.wellknown import label_ucdo_type, label_aucdo_arch
from debian_cloud_images.images.azure_partnerlegacy.s3_version import ImagesAzurePartnerlegacyVersion
from debian_cloud_images.images.azure_storage.s1_folder import ImagesAzureStorageFolder
from debian_cloud_images.images.azure_storage.s2_blob import ImagesAzureStorageBlob
from debian_cloud_images.utils.azure.image_version import AzureImageVersion
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver

from .base import cli
from .upload_base import UploadBaseCommand
from ..images.publicinfo import ImagePublicType
from ..utils import argparse_ext


@cli.register(
    'upload-azure-partner',
    usage='%(prog)s [MANIFEST]...',
    help='upload Debian images to Azure Partner offers',
    epilog='''
config options:
  azure.auth.client     application ID of service account, or empty for using az
  azure.auth.secret     secret of service account, or empty for using az
  azure.cloudpartner.tenant
  azure.cloudpartner.publisher
  azure.storage.tenant
  azure.storage.subscription
  azure.storage.group
  azure.storage.name
''',
    arguments=[
        cli.prepare_argument(
            'manifests',
            help='read manifests',
            metavar='MANIFEST',
            nargs='*',
            type=pathlib.Path
        ),
        cli.prepare_argument(
            '--output',
            default='.',
            help='write manifests to (default: .)',
            metavar='DIR',
            type=pathlib.Path
        ),
        cli.prepare_argument(
            '--variant',
            action=argparse_ext.ActionEnum,
            default='dev',
            dest='public_type',
            enum=ImagePublicType,
        ),
        cli.prepare_argument(
            '--version-override',
            dest='override_version',
        ),
        cli.prepare_argument(
            '--partner-offer',
            help='use specified offer inside Azure Partner interface',
            metavar='OFFER',
            required=True,
        ),
        cli.prepare_argument(
            '--partner-plan-override',
            help='use specified plan inside Azure Partner interface',
            metavar='PLAN',
        ),
        cli.prepare_argument(
            '--partner-version-override',
            help='use specified version inside Azure Partner interface',
            metavar='VERSION',
            type=AzureImageVersion.from_string,
        ),
    ],
)
class UploadAzurePartnerlegacyCommand(UploadBaseCommand):
    def __init__(
            self, *,
            partner_offer: str,
            partner_plan_override: str,
            partner_version_override: AzureImageVersion,
            **kw,
    ):
        super().__init__(**kw)

        self._partner_offer = partner_offer
        self._partner_plan_override = partner_plan_override
        self._partner_version_override = partner_version_override
        self._storage_folder = partner_offer

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._partner_tenant = str(self.config_get('azure.cloudpartner.tenant'))
        self._partner_publisher = self.config_get('azure.cloudpartner.publisher')

        self._storage_tenant = str(self.config_get('azure.storage.tenant'))
        self._storage_subscription = str(self.config_get('azure.storage.subscription'))
        self._storage_group = self.config_get('azure.storage.group')
        self._storage_name = self.config_get('azure.storage.name')

        if len(self.images) != 1:
            raise RuntimeError('Can only handle one image at a time')
        self.image = list(self.images.values())[0]

    def __call__(self) -> None:
        partner_conn = AzureGenericOAuth2Connection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._partner_tenant,
            subscription_id=None,
            host='cloudpartner.azure.com',
            login_resource='https://cloudpartner.azure.com',
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

        image_folder = ImagesAzureStorageFolder(
            self._storage_group,
            self._storage_name,
            self._storage_folder,
            storage_driver,
            storage_obj,
        )
        image_folder.create()

        try:
            image_public_info = self.image_public_info.apply(self.image.build_info)
            # XXX
            image_arch = self.config_image.archs[self.image.build_info['arch']]

            if self._partner_plan_override is not None:
                image_plan = self._partner_plan_override
            else:
                image_plan = self.image.build_info['release_id']

            if self._partner_version_override is not None:
                image_version = self._partner_version_override
            elif 'version_azure' in self.image.build_info:
                image_version = self.image.build_info['version_azure']
            else:
                raise RuntimeError('No Azure version, use --partner-version-override')

            image_ref = f'{self._partner_publisher}/{self._partner_offer}/{image_plan}/{image_version}'

            image_blob_name = f'{image_plan}:{image_arch.name}:{image_version}.vhd'
            image_blob = ImagesAzureStorageBlob(
                self._storage_group,
                self._storage_name,
                self._storage_folder,
                image_blob_name,
                storage_driver,
                storage_obj,
            )

            partner_version = ImagesAzurePartnerlegacyVersion(
                self._partner_publisher,
                self._partner_offer,
                image_plan,
                str(image_version),
                partner_conn,
            )

            print(f'Uploading image version: {image_ref}')

            with self.image.open_image('vhd') as f:
                image_blob.put(f)

            print(f'Creating image version: {image_ref}')

            query_sas = image_folder.query_sas(
                start=datetime.date.today() - datetime.timedelta(days=7),
                expiry=datetime.date.today() + datetime.timedelta(days=730),
                permission='rl',
            )

            versions = partner_version.create(
                url=f'{image_blob.url}?{query_sas}',
                image_arch=image_arch,
            )

            manifests = []

            for i in versions:
                metadata = self.image.build.metadata.copy()
                metadata.labels[label_ucdo_type] = image_public_info.public_type.name
                metadata.labels[label_aucdo_arch] = i['arch']

                manifests.append(Upload(
                    metadata=metadata,
                    provider='management.azure.com',
                    ref=i['ref'],
                    family_ref=i['family_ref'],
                ))

            self.image.write_manifests('upload-azure-partner', manifests, output=self.output)

            for i in versions:
                print(f'Created image version successfully: {i["ref"]}')

        except BaseException:
            raise


if __name__ == '__main__':
    cli.main(UploadAzurePartnerlegacyCommand)
