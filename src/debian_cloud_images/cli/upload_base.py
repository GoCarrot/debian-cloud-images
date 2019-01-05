import pathlib

from .base import BaseCommand
from ..images import Images


class UploadBaseCommand(BaseCommand):
    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--path',
            default='.',
            help='read manifests and images from (default: .)',
            metavar='PATH',
            type=pathlib.Path
        )
        parser.add_argument(
            '--variant',
            choices=('daily', 'dev', 'release'),
            default='dev',
        )
        parser.add_argument(
            '--version-override',
        )

    def __init__(self, *, path=None, **kw):
        super().__init__(**kw)

        self.images = Images()
        if path:
            self.images.read_path(path)

    def __call__(self):
        for image in self.images.values():
            self.uploader(image)
