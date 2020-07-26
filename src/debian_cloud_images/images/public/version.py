import logging
import os
import pathlib
import shutil
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
        self.__path = pathlib.Path(tempfile.mkdtemp(prefix=f'.{self.version}_', dir=self.basepath))
        self.__ref = self.baseref + self.version + '/'
        self.__images = []

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
        del self.__images

    def _commit(self):
        self._write_digest()
        self.__path.chmod(0o755)

        path = self.basepath / self.version
        pathbak = self.basepath / f'.{self.version}_{datetime.now().isoformat()}'

        if path.exists():
            logger.warning(f'Moving away existing directory {path} to {pathbak}')
            os.rename(path, pathbak)

        os.rename(self.__path, path)

    def _rollback(self):
        shutil.rmtree(self.__path.as_posix())

    def _write_digest(self):
        files = {}
        for i in self.__images:
            files.update(i.files)

        chfile = self.__path / 'SHA512SUMS'
        with chfile.open('w') as f:
            for n, d in sorted(files.items()):
                print(f'{d.hexdigest()}  {n}', file=f)
        chfile.chmod(0o444)

    def add_image(self, name, provider):
        i = Image(self.__path, self.__ref, name, provider)
        self.__images.append(i)
        return i
