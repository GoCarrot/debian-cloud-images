import os
import pathlib
import tempfile

from .image import Image


class Version:
    basepath: pathlib.Path
    baseref: str
    version: str

    def __init__(self, basepath: pathlib.Path, baseref: str, version: str):
        self.basepath = basepath
        self.baseref = baseref
        self.version = version

    def __enter__(self):
        self.__pathtmp = tempfile.TemporaryDirectory(prefix=f'.{self.version}_', dir=self.basepath)
        self.__path = self.basepath / self.version
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

        del self.__path
        del self.__pathtmp
        del self.__ref

    def _commit(self):
        os.rename(self.__pathtmp.name, self.__path)

    def _rollback(self):
        self.__pathtmp.cleanup()

    def add_image(self, name):
        return Image(self.__path, self.__ref, name)
