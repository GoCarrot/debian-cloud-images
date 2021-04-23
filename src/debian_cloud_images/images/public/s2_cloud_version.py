from __future__ import annotations

import collections.abc
import logging
import os
import pathlib
import shutil
import tempfile
import typing

from datetime import datetime

from .info import PublicInfo
from .s3_cloud_image import StepCloudImages
from ...utils.image_version import ImageVersion


logger = logging.getLogger(__name__)


class StepCloudVersion:
    name: ImageVersion
    basepath: pathlib.Path
    baseref: str
    images: StepCloudImages

    _info: PublicInfo

    def __init__(self, info: PublicInfo, name: ImageVersion, basepath: pathlib.Path, baseref: str) -> None:
        self._info = info
        self.name = name
        self.basepath = basepath
        self.baseref = baseref

    def __enter__(self) -> StepCloudVersion:
        raise NotImplementedError

    def __exit__(self, type, value, tb) -> None:
        raise NotImplementedError

    def delete(self) -> None:
        if not self._info.noop:
            path = self.basepath / str(self.name)
            shutil.rmtree(path)


class StepCloudVersionAdd(StepCloudVersion):
    def __enter__(self) -> StepCloudVersion:
        self.__path = path = pathlib.Path(tempfile.mkdtemp(prefix=f'.{self.name}_', dir=self.basepath))
        ref = self.baseref + str(self.name) + '/'

        self.__path_latest = self.__path / '.latest'
        self.__path_latest.mkdir(0o755, exist_ok=True)

        self.images = StepCloudImages(self._info, path, ref)

        return self

    def __exit__(self, type, value, tb) -> None:
        if tb is None:
            try:
                if not self._info.noop:
                    self._commit()
                else:
                    self._rollback()
            except BaseException:
                self._rollback()
                raise
        else:
            self._rollback()

        del self.__path
        del self.images

    def _commit(self):
        self._write_digest()
        self.__path.chmod(0o755)

        path = self.basepath / self.name
        pathbak = self.basepath / f'.{self.name}_{datetime.now().isoformat()}'

        if path.exists():
            logger.warning(f'Moving away existing directory {path} to {pathbak}')
            os.rename(path, pathbak)

        os.rename(self.__path, path)

        path_latest_tmp = pathlib.Path(tempfile.mktemp(prefix='.latest_', dir=self.basepath))
        path_latest = self.basepath / 'latest'

        path_latest_tmp.symlink_to(pathlib.Path(path.name) / '.latest')
        path_latest_tmp.rename(path_latest)

    def _rollback(self):
        logging.warning('Rolling back')
        shutil.rmtree(self.__path.as_posix())

    def _write_digest(self):
        files = {}
        files_latest = {}
        for i in self.images.values():
            files.update(i.files)
            files_latest.update(i.files_latest)

        chfile = self.__path / 'SHA512SUMS'
        with chfile.open('w') as f:
            for n, d in sorted(files.items()):
                print(f'{d.hexdigest()}  {n}', file=f)
        chfile.chmod(0o444)

        chfile = self.__path_latest / 'SHA512SUMS'
        with chfile.open('w') as f:
            for n, d in sorted(files_latest.items()):
                print(f'{d.hexdigest()}  {n}', file=f)
        chfile.chmod(0o444)


class StepCloudVersions(collections.abc.Mapping):
    _info: PublicInfo
    _basepath: pathlib.Path
    _baseref: str
    _children: typing.Dict[ImageVersion, StepCloudVersion]

    def __init__(self, info: PublicInfo, basepath: pathlib.Path, baseref: str) -> None:
        self._info = info
        self._basepath = basepath
        self._baseref = baseref
        self._children = {}

    def __delitem__(self, name: ImageVersion) -> None:
        self._children[name].delete()
        del self._children[name]

    def __getitem__(self, name: ImageVersion) -> StepCloudVersion:
        return self._children[name]

    def __iter__(self) -> typing.Iterator[ImageVersion]:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def add(self, name: ImageVersion) -> StepCloudVersion:
        return self._children.setdefault(name, StepCloudVersionAdd(self._info, name, self._basepath, self._baseref))

    def read(self) -> None:
        for path in self._basepath.iterdir():
            if path.is_dir():
                try:
                    version = ImageVersion.from_string(path.name)
                    self._children[version] = StepCloudVersion(self._info, version, self._basepath, self._baseref)

                except Exception:
                    logging.debug(f'Ignoring {path}, unparseable')

            else:
                logging.debug(f'Ignoring {path}, no dir')
