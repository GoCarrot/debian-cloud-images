import collections.abc
import logging
import typing

from .azure_version import AzureVersions
from .info import AzurePartnerInfo


logger = logging.getLogger(__name__)


class AzureSku:
    versions: AzureVersions

    _info: AzurePartnerInfo
    _name: str

    def __init__(self, info: AzurePartnerInfo, name, str) -> None:
        self._info = info
        self._name = name

        # TODO: provide data
        self.versions = AzureVersions(self._info, {})

    def __enter__(self) -> 'AzureSku':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass


class AzureSkus(collections.abc.Mapping):
    _info: AzurePartnerInfo
    _children: typing.Dict[str, AzureSku]

    def __init__(self, info: AzurePartnerInfo, data: typing.Any) -> None:
        self._info = info

        # TODO
        self._children = {}

    def __getitem__(self, name) -> AzureSku:
        return self._children[name]

    def __iter__(self) -> typing.Iterator:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)
