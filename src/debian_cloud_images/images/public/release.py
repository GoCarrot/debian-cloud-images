import pathlib

from .version import Version


class Release:
    basepath: pathlib.Path
    baseref: str
    name: str
    uploadtype: str

    def __init__(self, basepath: pathlib.Path, baseref: str, name: str, uploadtype: str):
        self.basepath = basepath
        self.baseref = baseref
        self.name = name
        self.uploadtype = uploadtype

    def __enter__(self):
        if not self.basepath.is_dir():
            raise RuntimeError(f'Storage path {self.basepath} does not exist, please create first')

        pathrelease = self.basepath / self.name
        pathrelease.mkdir(exist_ok=True)

        if self.uploadtype != 'release':
            self.__path = pathrelease / self.uploadtype
            self.__path.mkdir(exist_ok=True)
            self.__ref = self.baseref + self.name + '/' + self.uploadtype + '/'
        else:
            self.__path = pathrelease
            self.__ref = self.baseref + self.name + '/'

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
        del self.__ref

    def _commit(self):
        pass

    def _rollback(self):
        pass

    def add_version(self, version):
        return Version(self.__path, self.__ref, version)
