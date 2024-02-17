# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import pathlib

from .base import cli
from .upload_base import UploadBaseCommand
from ..images.public import PublicImages
from ..images.publicinfo import ImagePublicType
from ..utils import argparse_ext


logger = logging.getLogger(__name__)


@cli.register(
    'upload',
    usage='%(prog)s [MANIFEST]...',
    help='upload Debian images to own storage',
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
            '--provider',
            help='provider name',
            required=True,
        ),
        cli.prepare_argument(
            '--storage',
            help='base path for storage',
            metavar='PATH',
            required=True,
            type=pathlib.Path,
        ),
        cli.prepare_argument(
            '--no-op',
            action='store_true',
        ),
    ],
)
class UploadCommand(UploadBaseCommand):
    def __init__(
            self, *,
            no_op=True,
            provider=None,
            storage=None,
            **kw,
    ):
        super().__init__(**kw)

        self.no_op = no_op
        self.provider = provider
        self.storage = storage

    def __call__(self):
        PublicImages(
            self.no_op,
            self.image_public_info,
            self.image_public_info.public_type.name,
            self.storage,
            self.provider,
        ).add(self.images.values())


if __name__ == '__main__':
    cli.main(UploadCommand)
