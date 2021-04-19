import logging
import pathlib

from .upload_base import UploadBaseCommand
from ..images.public import PublicImages


logger = logging.getLogger(__name__)


class UploadCommand(UploadBaseCommand):
    argparser_name = 'upload'
    argparser_help = 'upload Debian images to own storage'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--provider',
            help='provider name',
            required=True,
        )
        parser.add_argument(
            '--storage',
            help='base path for storage',
            metavar='PATH',
            required=True,
            type=pathlib.Path,
        )
        parser.add_argument(
            '--no-op',
            action='store_true',
        )

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
    UploadCommand._main()
