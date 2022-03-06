import importlib.machinery
import importlib.resources
import pathlib
import platform
import typing


__spec__: importlib.machinery.ModuleSpec


def open_text(resource: str, encoding: str = 'utf-8', errors: str = 'strict') -> typing.TextIO:
    return importlib.resources.open_text(__spec__.name, resource, encoding, errors)


def path(resource: str) -> typing.ContextManager[pathlib.Path]:
    # XXX: Python < 3.10 fails if resource is not a real file or does not exist
    if tuple(int(i) for i in platform.python_version_tuple()[:2]) < (3, 10):
        loader = typing.cast(importlib.machinery.SourceFileLoader, __spec__.loader)
        return pathlib.Path(typing.cast(str, loader.path)).parent / resource
    return importlib.resources.path(__spec__.name, resource)
