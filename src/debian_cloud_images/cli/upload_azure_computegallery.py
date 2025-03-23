# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import logging
import pathlib
import secrets

from contextlib import ExitStack

from debian_cloud_images.api.cdo.upload import Upload
from debian_cloud_images.api.wellknown import label_ucdo_type
from debian_cloud_images.backend.azure import (
    AzureVmArch,
    AzureVmGeneration,
)
from debian_cloud_images.backend.azure.client import AzureClient
from debian_cloud_images.backend.azure.subscription import AzureSubscription
from debian_cloud_images.backend.azure.resourcegroup import AzureResourcegroup
from debian_cloud_images.backend.azure.computedisk import AzureComputedisk
from debian_cloud_images.backend.azure.computegallery import AzureComputegallery
from debian_cloud_images.backend.azure.computegallery_image import AzureComputegalleryImage
from debian_cloud_images.backend.azure.computegallery_image_version import AzureComputegalleryImageVersion
from debian_cloud_images.utils.azure.image_version import AzureImageVersion

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
        client: AzureClient
        if self._client_id and self._client_secret:
            client = AzureClient.auth_service_account(self._tenant, self._client_id, self._client_secret)
        else:
            client = AzureClient()

        with client as client:
            self._run(client)

    def _run(self, client: AzureClient) -> None:
        subscription = AzureSubscription(
            client,
            self._subscription,
        )
        group = AzureResourcegroup(
            subscription,
            self._group,
        )

        for image in self.images.values():
            with ExitStack() as cleanup, ExitStack() as cleanup_fail:
                image_arch = AzureVmArch[image.build_info['arch']]

                disk_name = f'{self._computegallery}-upload-{secrets.token_urlsafe(4)}'

                if self.computegallery_version_override is not None:
                    image_version = self.computegallery_version_override
                elif 'version_azure' in image.build_info:
                    image_version = image.build_info['version_azure']
                else:
                    raise RuntimeError('No Azure version, use --computegallery-version-override')

                computegallery = AzureComputegallery(
                    group,
                    self._computegallery,
                )

                computegallery_image = AzureComputegalleryImage(
                    computegallery,
                    self._computegallery,
                )

                computegallery_image_arch = AzureVmArch(computegallery_image.properties()['architecture'])
                computegallery_image_generation = AzureVmGeneration(computegallery_image.properties()['hyperVGeneration'])

                if computegallery_image_arch != image_arch:
                    raise RuntimeError('Image architecture does not match gallery image architecture')

                with image.open_image('vhd') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(0, 0)

                    computedisk = AzureComputedisk.create(
                        group,
                        disk_name,
                        arch=computegallery_image_arch,
                        generation=computegallery_image_generation,
                        size=size,
                    )

                    @cleanup.callback
                    def cleanup_computedisk(*exc_details) -> None:
                        try:
                            computedisk.delete()
                        except BaseException:
                            logger.exception('Failed to cleanup Azure disk')

                    logger.info(f'Uploading Azure disk: {disk_name}')

                    computedisk.upload(f)

                logger.info(f'Creating image version: {image_version}')

                computegallery_version = AzureComputegalleryImageVersion.create(
                    computegallery_image,
                    str(image_version),
                    disk=computedisk,
                    wait=self.wait,
                )

                @cleanup_fail.callback
                def cleanup_computegallery_version(*exc_details) -> None:
                    try:
                        computegallery_version.delete()
                    except BaseException:
                        logger.exception('Failed to cleanup Azure image version')

                metadata = image.build.metadata.copy()
                metadata.labels[label_ucdo_type] = self.image_public_info.apply(image.build_info).public_type.name

                manifests = [Upload(
                    metadata=metadata,
                    # TODO
                    provider='https://management.azure.com',
                    family_ref=computegallery_version.path.rsplit('/', 2)[0],
                    ref=computegallery_version.path,
                )]

                image.write_manifests('upload-azure-computegallery', manifests, output=self.output)

                logging.info(f'Created image version successfully: {computegallery_version.path}')

                # We are succesful, don't need to clean it up
                cleanup_fail.pop_all()

                # Image is read in the background, so can't delete if we don't wait
                if not self.wait:
                    cleanup.pop_all()
                    logging.info('Not deleting disk')


if __name__ == '__main__':
    cli.main(UploadAzureComputegalleryCommand)
