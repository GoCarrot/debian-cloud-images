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
        self.__dirtmp = tempfile.TemporaryDirectory(prefix=f'.{self.version}_', dir=self.basepath)
        self.__pathtmp = pathlib.Path(self.__dirtmp.name)
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

        del self.__dirtmp
        del self.__path
        del self.__pathtmp
        del self.__ref

    def _commit(self):
        os.rename(self.__pathtmp, self.__path)

    def _rollback(self):
        self.__dirtmp.cleanup()

    def add_image(self, name, provider):
        return Image(self.__pathtmp, self.__ref, name, provider)
