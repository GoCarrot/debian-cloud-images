import logging
import os
import pathlib
import tempfile

from datetime import datetime

from .image import Image


logger = logging.getLogger(__name__)


class Version:
    basepath: pathlib.Path
    baseref: str
    version: str

    def __init__(self, basepath: pathlib.Path, baseref: str, version: str):
        self.basepath = basepath
        self.baseref = baseref
        self.version = version

    def __enter__(self):
        self.__tmp = tempfile.TemporaryDirectory(prefix=f'.{self.version}_', dir=self.basepath)
        self.__path = pathlib.Path(self.__tmp.name)
        self.__ref = self.baseref + self.version + '/'

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

        del self.__tmp
        del self.__path
        del self.__ref

    def _commit(self):
        path = self.basepath / self.version
        pathbak = self.basepath / f'.{self.version}_{datetime.now().isoformat()}'

        if path.exists():
            logger.warning(f'Moving away existing directory {path} to {pathbak}')
            os.rename(path, pathbak)

        os.rename(self.__path, path)

    def _rollback(self):
        self.__tmp.cleanup()

    def add_image(self, name, provider):
        return Image(self.__path, self.__ref, name, provider)
