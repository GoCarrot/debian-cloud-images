import pathlib


class Image:
    basepath: pathlib.Path
    baseref: str
    imagename: str

    def __init__(self, basepath: pathlib.Path, baseref: str, imagename: str):
        self.basepath = basepath
        self.baseref = baseref
        self.imagename = imagename

    def __enter__(self):
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

    def _commit(self):
        pass

    def _rollback(self):
        pass
