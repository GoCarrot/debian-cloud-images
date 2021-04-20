from __future__ import annotations

import base64
import hashlib
import json
import logging
import pathlib
import typing

from ...api.cdo.upload import Upload
from ...api.registry import registry as api_registry
from ...api.wellknown import annotation_cdo_digest, label_ucdo_image_format, label_ucdo_type
from ...utils.files import ChunkedFile


logger = logging.getLogger(__name__)


class Image:
    basepath: pathlib.Path
    baseref: str
    imagename: str
    provider: str

    files: typing.Dict[str, hashlib._Hash]
    manifests: typing.List

    def __init__(self, basepath: pathlib.Path, baseref: str, imagename: str, provider: str):
        self.basepath = basepath
        self.baseref = baseref
        self.imagename = imagename
        self.provider = provider

    def __enter__(self):
        self.files = {}
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
        path = self.__path.with_suffix('.json')
        output_hash = hashlib.sha512()

        with path.open('wb') as f:
            s = json.dumps(api_registry.dump(manifests), indent=4, separators=(',', ': '), sort_keys=True)
            s = s.encode('utf-8')
            f.write(s)
            output_hash.update(s)
        path.chmod(0o444)

        self._append_file(path, output_hash)

    def _rollback(self):
        pass

    def write(self, image, public_type):
        self.__manifests_input.append(image.build)

        self._copy_tar(image, public_type)

        if image.build_vendor in ('generic', 'genericcloud', 'nocloud'):
            self._copy_converted(image, public_type)

    def _copy_converted(self, image, public_type):
        with image.open_image(None, 'qcow2') as (f_in_raw, f_in_qcow2):
            self._copy_raw(f_in_raw, image, public_type)
            self._copy_qcow2(f_in_qcow2, image, public_type)

    def _copy_qcow2(self, f_in, image, public_type):
        path = self.__path.with_suffix('.qcow2')
        ref = self.__ref + '.qcow2'
        logger.info(f'Copy to {ref}')
        with path.open('wb') as f_out:
            output_hash = self.__copy_hash(f_in, f_out)
        path.chmod(0o444)

        self._append_manifest(image, public_type, ref, 'qcow2', output_hash)
        self._append_file(path, output_hash)

    def _copy_raw(self, f_in, image, public_type):
        path = self.__path.with_suffix('.raw')
        ref = self.__ref + '.raw'
        logger.info(f'Copy to {ref}')
        with path.open('wb') as f_out:
            output_hash = hashlib.sha512()
            chunked = ChunkedFile(f_in, 4 * 1024 * 1024)
            for chunk in chunked:
                data = chunk.read()
                output_hash.update(data)
                if chunk.is_data:
                    f_out.seek(chunk.offset)
                    f_out.write(data)
            f_out.truncate(chunked.size)
        path.chmod(0o444)

        self._append_manifest(image, public_type, ref, 'raw', output_hash)
        self._append_file(path, output_hash)

    def _copy_tar(self, image, public_type):
        with image.open_tar_raw() as f_in:
            path = self.__path.with_suffix(f_in.extension)
            ref = self.__ref + f_in.extension
            logger.info(f'Copy to {ref}')
            with path.open('wb') as f_out:
                output_hash = self.__copy_hash(f_in, f_out)
            path.chmod(0o444)

        self._append_manifest(image, public_type, ref, 'internal', output_hash)
        self._append_file(path, output_hash)

    def __copy_hash(self, f_in, f_out, length=64 * 1024):
        output_hash = hashlib.sha512()

        with memoryview(bytearray(length)) as mv:
            while True:
                n = f_in.readinto(mv)
                if not n:
                    break
                elif n < length:
                    with mv[:n] as smv:
                        f_out.write(smv)
                        output_hash.update(smv)
                else:
                    f_out.write(mv)
                    output_hash.update(mv)

        return output_hash

    def _append_manifest(self, image, public_type, ref, image_format, output_hash):
        output_digest = base64.b64encode(output_hash.digest()).decode().rstrip('=')

        metadata = image.build.metadata.copy()
        metadata.annotations[annotation_cdo_digest] = f'{output_hash.name}:{output_digest}'
        metadata.labels[label_ucdo_image_format] = image_format
        metadata.labels[label_ucdo_type] = public_type

        self.manifests.append(Upload(
            metadata=metadata,
            provider=self.provider,
            ref=ref,
        ))

    def _append_file(self, path, output_hash):
        self.files[path.name] = output_hash
