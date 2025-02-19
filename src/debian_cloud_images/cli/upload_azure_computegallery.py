# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import logging
import pathlib
import secrets

from typing import (
    Any,
    cast,
)

from debian_cloud_images.api.cdo.upload import Upload
from debian_cloud_images.api.wellknown import label_ucdo_type
from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup
from debian_cloud_images.images.azure.computedisk import (
    ImagesAzureComputedisk,
    ImagesAzureComputediskArch,
    ImagesAzureComputediskGeneration,
)
from debian_cloud_images.images.azure.computegallery import ImagesAzureComputegallery
from debian_cloud_images.images.azure.computegallery_image import ImagesAzureComputegalleryImage
from debian_cloud_images.images.azure.computegallery_image_version import ImagesAzureComputegalleryImageVersion
from debian_cloud_images.utils.azure.image_version import AzureImageVersion
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

from .base import cli
from .upload_base import UploadBaseCommand
from ..images.publicinfo import ImagePublicType
from ..utils import argparse_ext


logger = logging.getLogger(__name__)


@cli.register(
    'upload-azure-computegallery',
    usage='%(prog)s [MANIFEST]...',
    help='upload Debian images to Azure Compute Gallery',
    epilog='''
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
            '--computegallery-image',
            help='use specified image inside Azure Compute Gallery',
            metavar='IMAGE',
            required=True,
        ),
        cli.prepare_argument(
            '--computegallery-version-override',
            help='use specified image version inside Azure Compute Gallery',
            metavar='VERSION',
            type=AzureImageVersion.from_string,
        ),
        cli.prepare_argument(
            '--wait',
            default=True,
            help='wait for long running operation',
            action=argparse.BooleanOptionalAction,
        ),
    ],
)
class UploadAzureComputegalleryCommand(UploadBaseCommand):
    computegallery_image: str
    computegallery_version_override: AzureImageVersion
    wait: bool

    def __init__(
            self, *,
            computegallery_image: str,
            computegallery_version_override: AzureImageVersion,
            wait: bool,
            **kw,
    ) -> None:
        super().__init__(**kw)

        self.computegallery_image = computegallery_image
        self.computegallery_version_override = computegallery_version_override
        self.wait = wait

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._tenant = str(self.config_get('azure.computegallery.tenant'))
        self._subscription = str(self.config_get('azure.computegallery.subscription'))
        self._group = self.config_get('azure.computegallery.group')
        self._computegallery = self.config_get('azure.computegallery.name')

        if len(self.images) > 1:
            raise RuntimeError('Can only handle one image at a time')

    def __call__(self) -> None:
        computedisk: ImagesAzureComputedisk | None = None
        computegallery_version: ImagesAzureComputegalleryImageVersion | None = None

        conn = AzureGenericOAuth2Connection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._tenant,
            subscription_id=self._subscription,
            host='management.azure.com',
            login_resource='https://management.core.windows.net/',
        )

        group = ImagesAzureResourcegroup(
            self._group,
            conn,
        )

        for image in self.images.values():
            try:
                image_arch = ImagesAzureComputediskArch[image.build_info['arch']]

                disk_name = f'{self._computegallery}-upload-{secrets.token_urlsafe(4)}'

                if self.computegallery_version_override is not None:
                    image_version = self.computegallery_version_override
                elif 'version_azure' in image.build_info:
                    image_version = image.build_info['version_azure']
                else:
                    raise RuntimeError('No Azure version, use --computegallery-version-override')

                computegallery = ImagesAzureComputegallery(
                    group,
                    self._computegallery,
                    conn,
                )

                computegallery_image = ImagesAzureComputegalleryImage(
                    computegallery,
                    self._computegallery,
                    conn,
                )

                computegallery_image_arch = ImagesAzureComputediskArch(computegallery_image.properties['architecture'])
                computegallery_image_generation = ImagesAzureComputediskGeneration(computegallery_image.properties['hyperVGeneration'])

                if computegallery_image_arch != image_arch:
                    raise RuntimeError('Image architecture does not match gallery image architecture')

                with image.open_image('vhd') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(0, 0)

                    computedisk = ImagesAzureComputedisk.create(
                        group,
                        disk_name,
                        conn,
                        arch=computegallery_image_arch,
                        generation=computegallery_image_generation,
                        size=size,
                    )

                    logger.info(f'Uploading Azure disk: {disk_name}')

                    computedisk.upload(f)

                logger.info(f'Creating image version: {image_version}')

                computegallery_version = ImagesAzureComputegalleryImageVersion.create(
                    computegallery_image,
                    str(image_version),
                    conn,
                    disk=computedisk,
                    wait=self.wait,
                )

                metadata = image.build.metadata.copy()
                metadata.labels[label_ucdo_type] = self.image_public_info.apply(image.build_info).public_type.name

                manifests = [Upload(
                    metadata=metadata,
                    provider=cast(Any, conn.connection).host,
                    family_ref=computegallery_version.path.rsplit('/', 2)[0],
                    ref=computegallery_version.path,
                )]

                image.write_manifests('upload-azure-computegallery', manifests, output=self.output)

                logging.info(f'Created image version successfully: {computegallery_version.path}')

                # We are succesful, don't need to clean it up
                computegallery_version = None

                # Image is read in the background, so can't delete if we don't wait
                if not self.wait:
                    computedisk = None
                    logging.info('Not deleting disk')

            finally:
                if computegallery_version:
                    try:
                        computegallery_version.delete()
                    except BaseException:
                        logger.exception('Failed to cleanup Azure image version')

                if computedisk:
                    try:
                        computedisk.delete()
                    except BaseException:
                        logger.exception('Failed to cleanup Azure disk')


if __name__ == '__main__':
    cli.main(UploadAzureComputegalleryCommand)
