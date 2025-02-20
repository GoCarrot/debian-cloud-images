# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import logging
import pathlib

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
from debian_cloud_images.images.azure.computeimage import ImagesAzureComputeimage
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

from .base import cli
from .upload_base import UploadBaseCommand
from ..images.publicinfo import ImagePublicType
from ..utils import argparse_ext


logger = logging.getLogger(__name__)


@staticmethod
@cli.register(
    'upload-azure',
    usage='%(prog)s [MANIFEST]...',
    help='upload Debian images to Azure Compute',
    epilog='''
config options:
  azure.auth.client     application ID of service account, or empty for using az
  azure.auth.secret     secret of service account, or empty for using az
  azure.image.tenant
  azure.image.subscription
  azure.image.group
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
            '--location',
        ),
        cli.prepare_argument(
            '--generation',
            choices=(1, 2),
            default=2,
            type=int,
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
            '--wait',
            default=True,
            help='wait for long running operation',
            action=argparse.BooleanOptionalAction,
        ),
    ],
)
class UploadAzureCommand(UploadBaseCommand):
    location: str | None
    generation: ImagesAzureComputediskGeneration
    wait: bool

    def __init__(
            self,
            *,
            location: str | None,
            generation: int,
            wait: bool,
            **kw,
    ) -> None:
        super().__init__(**kw)

        self.location = location
        self.generation = ImagesAzureComputediskGeneration[f'v{generation}']
        self.wait = wait

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._tenant = str(self.config_get('azure.image.tenant'))
        self._subscription = str(self.config_get('azure.image.subscription'))
        self._group = self.config_get('azure.image.group')

        if len(self.images) > 1:
            raise RuntimeError('Can only handle one image at a time')

    def __call__(self) -> None:
        computedisk: ImagesAzureComputedisk | None = None
        computeimage: ImagesAzureComputeimage | None = None

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
                image_public_info = self.image_public_info.apply(image.build_info)
                image_name = image_public_info.vendor_name_extra(self.generation.name)

                if image_arch is not ImagesAzureComputediskArch.amd64:
                    raise RuntimeError('Image architecture must be amd64')

                with image.open_image('vhd') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(0, 0)

                    computedisk = ImagesAzureComputedisk.create(
                        group,
                        image_name,
                        conn,
                        arch=image_arch,
                        generation=self.generation,
                        size=size,
                    )

                    logger.info(f'Uploading Azure disk: {image_name}')

                    computedisk.upload(f)

                    logger.info(f'Creating Azure image: {image_name}')

                    computeimage = ImagesAzureComputeimage.create(
                        group,
                        image_name,
                        conn,
                        disk=computedisk,
                        wait=self.wait,
                    )

                metadata = image.build.metadata.copy()
                metadata.labels[label_ucdo_type] = image_public_info.public_type.name

                manifests = [Upload(
                    metadata=metadata,
                    provider=cast(Any, conn.connection).host,
                    ref=computeimage.path,
                )]

                image.write_manifests('upload-azure', manifests, output=self.output)

                logger.info(f'Created image successfully: {computeimage.path}')

                # We are succesful, don't need to clean it up
                computeimage = None

            finally:
                if computeimage:
                    try:
                        computeimage.delete()
                    except BaseException:
                        logger.exception('Failed to cleanup Azure image')

                if computedisk:
                    try:
                        computedisk.delete()
                    except BaseException:
                        logger.exception('Failed to cleanup Azure disk')


if __name__ == '__main__':
    cli.main(UploadAzureCommand)
