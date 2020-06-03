import json
import logging
import pathlib
import shutil

from ...api.cdo.upload import Upload
from ...api.registry import registry as api_registry
from ...api.wellknown import label_ucdo_image_format, label_ucdo_type


logger = logging.getLogger(__name__)


class Image:
    basepath: pathlib.Path
    baseref: str
    imagename: str
    provider: str

    def __init__(self, basepath: pathlib.Path, baseref: str, imagename: str, provider: str):
        self.basepath = basepath
        self.baseref = baseref
        self.imagename = imagename
        self.provider = provider

    def __enter__(self):
        self.manifests = []
        self.__manifests_input = []
        self.__path = self.basepath / self.imagename
        self.__ref = self.baseref + self.imagename

        return self

    def __exit__(self, type, value, tb):
        if tb is None:
            try:
                self._commit()
            except BaseException:
                self._rollback()
                raise
        else:
            self._rollback()

        del self.__manifests_input
        del self.__path
        del self.__ref

    def _commit(self):
        manifests = self.__manifests_input + self.manifests

        with self.__path.with_suffix('.json').open('w') as f:
            json.dump(api_registry.dump(manifests), f, indent=4, separators=(',', ': '), sort_keys=True)

    def _rollback(self):
        pass

    def write(self, image, public_type):
        self.__manifests_input.append(image.build)

        self._copy_tar(image, public_type)

        if image.build_vendor in ('generic', 'genericcloud', 'nocloud'):
            self._copy_qcow2(image, public_type)

    def _copy_qcow2(self, image, public_type):
        with image.open_image('qcow2') as f_in:
            path = self.__path.with_suffix('.qcow2')
            ref = self.__ref + '.qcow2'
            logger.info(f'Copy to {ref}')
            with path.open('wb') as f:
                shutil.copyfileobj(f_in, f)

        self._append_manifest(image, public_type, ref, 'qcow2')

    def _copy_tar(self, image, public_type):
        with image.open_tar_raw() as f_in:
            path = self.__path.with_suffix(f_in.extension)
            ref = self.__ref + f_in.extension
            logger.info(f'Copy to {ref}')
            with path.open('wb') as f:
                shutil.copyfileobj(f_in, f)

        self._append_manifest(image, public_type, ref, 'internal')

    def _append_manifest(self, image, public_type, ref, image_format):
        metadata = image.build.metadata.copy()
        metadata.labels[label_ucdo_image_format] = image_format
        metadata.labels[label_ucdo_type] = public_type

        self.manifests.append(Upload(
            metadata=metadata,
            provider=self.provider,
            ref=ref,
        ))
