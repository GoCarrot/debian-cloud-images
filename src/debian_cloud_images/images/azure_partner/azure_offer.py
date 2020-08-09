import collections.abc
import logging
import typing

from .azure_sku import AzureSkus
from .info import AzurePartnerInfo


logger = logging.getLogger(__name__)


class AzureOffer:
    skus: AzureSkus

    _info: AzurePartnerInfo
    _name: str

    def __init__(self, info: AzurePartnerInfo, name: str) -> None:
        self._info = info
        self._name = name

        # TODO: provide data
        self.skus = AzureSkus(self._info, {})

    def __enter__(self) -> 'AzureOffer':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass


class AzureOffers(collections.abc.Mapping):
    _info: AzurePartnerInfo

    def __init__(self, info: AzurePartnerInfo) -> None:
        self._info = info

    def __getitem__(self, name) -> AzureOffer:
        return AzureOffer(self._info, name)

    def __iter__(self) -> typing.Iterator:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
