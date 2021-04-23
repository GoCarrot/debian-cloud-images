from __future__ import annotations

import base64
import collections.abc
import hashlib
import json
import logging
import pathlib
import typing

from ...api.cdo.upload import Upload
from ...api.registry import registry as api_registry
from ...api.wellknown import annotation_cdo_digest, label_ucdo_image_format, label_ucdo_type
from ...utils.files import ChunkedFile

from .info import PublicInfo


logger = logging.getLogger(__name__)


class StepCloudImage:
    name: str
    family: str
    basepath: pathlib.Path
    baseref: str

    files: typing.Dict[str, hashlib._Hash]
    manifests: typing.List

    def __init__(self, info: PublicInfo, name: str, family: str, basepath: pathlib.Path, baseref: str) -> None:
        self._info = info
        self.name = name
        self.family = family
        self.basepath = basepath
        self.baseref = baseref

    def __enter__(self):
        self.files = {}
        self.files_latest = {}
        self.manifests = []
        self.__manifests_input = []
        self.__path = self.basepath / self.name
        self.__ref = self.baseref + self.name

        path_latest = self.basepath / '.latest'
        self.__path_latest = path_latest / self.family

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
        path_latest = self.__path_latest.with_suffix('.json')
        output_hash = hashlib.sha512()

        with path.open('wb') as f:
            s = json.dumps(api_registry.dump(manifests), indent=4, separators=(',', ': '), sort_keys=True)
            s = s.encode('utf-8')
            f.write(s)
            output_hash.update(s)
        path.chmod(0o444)

        path_latest.symlink_to(pathlib.Path('..') / path.name)

        self._append_file(path, path_latest, output_hash)

    def _rollback(self):
        pass

    def write(self, image):
        self.__manifests_input.append(image.build)

        self._copy_tar(image)

        if image.build_vendor in ('generic', 'genericcloud', 'nocloud'):
            self._copy_converted(image)

    def _copy_converted(self, image):
        with image.open_image(None, 'qcow2') as (f_in_raw, f_in_qcow2):
            self._copy_raw(f_in_raw, image)
            self._copy_qcow2(f_in_qcow2, image)

    def _copy_qcow2(self, f_in, image):
        path = self.__path.with_suffix('.qcow2')
        path_latest = self.__path_latest.with_suffix('.qcow2')
        ref = self.__ref + '.qcow2'
        logger.info(f'Copy to {ref}')
        with path.open('wb') as f_out:
            output_hash = self.__copy_hash(f_in, f_out)
        path.chmod(0o444)

        path_latest.symlink_to(pathlib.Path('..') / path.name)

        self._append_manifest(image, ref, 'qcow2', output_hash)
        self._append_file(path, path_latest, output_hash)

    def _copy_raw(self, f_in, image):
        path = self.__path.with_suffix('.raw')
        path_latest = self.__path_latest.with_suffix('.raw')
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

        path_latest.symlink_to(pathlib.Path('..') / path.name)

        self._append_manifest(image, ref, 'raw', output_hash)
        self._append_file(path, path_latest, output_hash)

    def _copy_tar(self, image):
        with image.open_tar_raw() as f_in:
            path = self.__path.with_suffix(f_in.extension)
            path_latest = self.__path_latest.with_suffix(f_in.extension)
            ref = self.__ref + f_in.extension

            logger.info(f'Copy to {ref}')
            with path.open('wb') as f_out:
                output_hash = self.__copy_hash(f_in, f_out)
            path.chmod(0o444)

            path_latest.symlink_to(pathlib.Path('..') / path.name)

        self._append_manifest(image, ref, 'internal', output_hash)
        self._append_file(path, path_latest, output_hash)

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

    def _append_manifest(self, image, ref, image_format, output_hash):
        output_digest = base64.b64encode(output_hash.digest()).decode().rstrip('=')

        metadata = image.build.metadata.copy()
        metadata.annotations[annotation_cdo_digest] = f'{output_hash.name}:{output_digest}'
        metadata.labels[label_ucdo_image_format] = image_format
        metadata.labels[label_ucdo_type] = self._info.public_type

        self.manifests.append(Upload(
            metadata=metadata,
            provider=self._info.provider,
            ref=ref,
        ))

    def _append_file(self, path, path_latest, output_hash):
        self.files[path.name] = output_hash
        self.files_latest[path_latest.name] = output_hash


class StepCloudImages(collections.abc.Mapping):
    _info: PublicInfo
    _basepath: pathlib.Path
    _baseref: str
    _children: typing.Dict[str, StepCloudImage]

    def __init__(self, info: PublicInfo, basepath: pathlib.Path, baseref: str) -> None:
        self._info = info
        self._basepath = basepath
        self._baseref = baseref
        self._children = {}

    def __getitem__(self, name) -> StepCloudImage:
        return self._children[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def add(self, name: str, family: str) -> StepCloudImage:
        return self._children.setdefault(name, StepCloudImage(self._info, name, family, self._basepath, self._baseref))
