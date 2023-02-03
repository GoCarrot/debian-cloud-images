import importlib.machinery
import pathlib
import typing


# XXX: mypy stub files lack get_resource_reader
class SourceFileLoader(importlib.machinery.SourceFileLoader):
    def get_resource_reader(self) -> typing.Any:
        ...


__spec__: importlib.machinery.ModuleSpec
__loader = typing.cast(SourceFileLoader, __spec__.loader)


def open_text(resource: str, encoding: str = 'utf-8', errors: str = 'strict') -> typing.TextIO:
    return path(resource).open('r', encoding=encoding, errors=errors)


def path(resource: str) -> pathlib.Path:
    files = getattr(__loader.get_resource_reader(), 'files', None)

    # Python < 3.10 does not have files()
    if files is None:
        def files():
            return pathlib.Path(__loader.path).parent

    return files() / resource
