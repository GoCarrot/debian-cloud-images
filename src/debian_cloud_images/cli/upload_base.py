import pathlib

from .base import BaseCommand
from ..images import Images
from ..images.publicinfo import ImagePublicInfo, ImagePublicType
from ..utils import argparse_ext


class UploadBaseCommand(BaseCommand):
    argparser_usage = '%(prog)s [MANIFEST]...'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            'manifests',
            help='read manifests',
            metavar='MANIFEST',
            nargs='*',
            type=pathlib.Path
        )
        parser.add_argument(
            '--output',
            default='.',
            help='write manifests to (default: .)',
            metavar='DIR',
            type=pathlib.Path
        )
        parser.add_argument(
            '--variant',
            action=argparse_ext.ActionEnum,
            default='dev',
            dest='public_type',
            enum=ImagePublicType,
        )
        parser.add_argument(
            '--version-override',
            dest='override_version',
        )

    def __init__(self, *, manifests=[], output=None, public_type=None, override_version=None, **kw):
        super().__init__(**kw)

        self.output = output

        override_info = {}
        if override_version:
            override_info['version'] = override_version
        self.image_public_info = ImagePublicInfo(public_type=public_type, override_info=override_info)

        self.images = Images()
        for manifest in manifests:
            self.images.read(manifest)

    def __call__(self):
        for image in self.images.values():
            self.uploader(image, public_info=self.image_public_info.apply(image.build_info))
