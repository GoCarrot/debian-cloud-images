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

    __api_data: typing.Any

    def __init__(self, info: AzurePartnerInfo, api_data: typing.Any) -> None:
        self._info = info
        self.__api_data = api_data

        self._name = api_data['planId']

        self.versions = AzureVersions(self._info, api_data)

    def __enter__(self) -> 'AzureSku':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass


class AzureSkus(collections.abc.Mapping):
    _info: AzurePartnerInfo
    _children: typing.Dict[str, AzureSku]

    def __init__(self, info: AzurePartnerInfo, api_data: typing.Any) -> None:
        self._info = info

        self._children = {i['planId']: AzureSku(self._info, i) for i in api_data}

    def __getitem__(self, name) -> AzureSku:
        return self._children[name]

    def __iter__(self) -> typing.Iterator:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)
