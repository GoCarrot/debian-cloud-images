import logging
import pathlib
import shutil

from .upload_base import UploadBaseCommand
from ..api.cdo.upload import Upload
from ..api.wellknown import label_ucdo_image_format, label_ucdo_type


class ImageUploader:
    def __init__(self, output, provider, storage):
        self.output = output
        self.provider = provider
        self.storage = storage

    def __call__(self, image, public_info):
        try:
            base_path = self.storage / public_info.path
            base_ref = pathlib.Path(public_info.path)

            base_path.parent.mkdir(parents=True, exist_ok=True)

            manifests = []
            manifests.append(self.copy(image, public_info, base_path, base_ref))

            if image.build_vendor in ('generic', 'genericcloud', 'nocloud'):
                manifests.append(self.copy_qcow2(image, public_info, base_path, base_ref))

        finally:
            with base_path.with_suffix('.json').open('w') as f:
                image.write_merged_manifests(f, manifests)
            image.write_manifests('upload', manifests, output=self.output)

    def copy(self, image, public_info, base_path, base_ref):
        with image.open_tar_raw() as f_in:
            path = base_path.with_suffix(f_in.extension)
            ref = base_ref.with_suffix(f_in.extension)
            logging.info(f'Copy to {path.as_posix()} ({ref})')
            with path.open('wb') as f:
                shutil.copyfileobj(f_in, f)

        return self.generate_manifest(image, public_info, ref, 'internal')

    def copy_qcow2(self, image, public_info, base_path, base_ref):
        with image.open_image('qcow2') as f_in:
            path = base_path.with_suffix('.qcow2')
            ref = base_ref.with_suffix('.qcow2')
            logging.info(f'Copy as qcow2 to {path.as_posix()} ({ref})')
            with path.open('wb') as f:
                shutil.copyfileobj(f_in, f)

        return self.generate_manifest(image, public_info, ref, 'qcow2')

    def generate_manifest(self, image, public_info, ref, image_format):
        metadata = image.build.metadata.copy()
        metadata.labels[label_ucdo_image_format] = image_format
        metadata.labels[label_ucdo_type] = public_info.public_type.name

        return Upload(
            metadata=metadata,
            provider=self.provider,
            ref=ref,
        )


class UploadCommand(UploadBaseCommand):
    argparser_name = 'upload'
    argparser_help = 'upload Debian images to own storage'

    @classmethod
    def _argparse_register(cls, parser, config):
        super()._argparse_register(parser, config)

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


if __name__ == '__main__':
    UploadCommand._main()
