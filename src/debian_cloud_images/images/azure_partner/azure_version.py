import collections.abc
import logging
import typing

from .info import AzurePartnerInfo


logger = logging.getLogger(__name__)


class AzureVersion:
    _info: AzurePartnerInfo
    _name: str

    def __init__(self, info: AzurePartnerInfo, name: str) -> None:
        self._info = info
        self._name = name

    def __enter__(self) -> 'AzureVersion':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass


class AzureVersions(collections.abc.Mapping):
    _info: AzurePartnerInfo
    _children: typing.Dict[str, AzureVersion]

    def __init__(self, info: AzurePartnerInfo, data: typing.Any) -> None:
        self._info = info

        # TODO
        self._children = {}

    def __getitem__(self, name) -> AzureVersion:
        return self._children[name]

    def __iter__(self) -> typing.Iterator:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)
