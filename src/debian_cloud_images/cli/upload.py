import itertools
import logging
import pathlib

from .upload_base import UploadBaseCommand
from ..images.public.release import Release


logger = logging.getLogger(__name__)


class ImageUploader:
    def __init__(self, output, provider, storage):
        self.output = output
        self.provider = provider
        self.storage = storage

    def __call__(self, images, public_info):
        for name, images_release in self.groupby_complete(images.values(), key=lambda i: i.build_release):
            with Release(self.storage, '', name, public_info.public_type.name) as s:
                logging.debug(f'Handle release {name}')
                self.do_release(s, images_release, public_info)

    def do_release(self, release, images, public_info):
        for name, images_version in self.groupby_complete(images, key=lambda i: i.build_version):
            with release.add_version(name) as s:
                logging.debug(f'Handle version {name}')
                self.do_version(s, images_version, public_info)

    def do_version(self, version, images, public_info):
        for image in images:
            info = public_info.apply(image.build_info)
            name = info.name
            with version.add_image(name, self.provider) as s:
                logging.debug(f'Handle image {name}')
                s.write(image, info.public_type.name)
                image.write_manifests('upload', s.manifests, output=self.output)

    def groupby_complete(self, iterable, key):
        return itertools.groupby(sorted(iterable, key=key), key=key)


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

    def __init__(self, *, provider=None, storage=None, **kw):
        super().__init__(**kw)

        self.uploader = ImageUploader(
            output=self.output,
            provider=provider,
            storage=storage,
        )

    def __call__(self):
        self.uploader(self.images, self.image_public_info)


if __name__ == '__main__':
    UploadCommand._main()
