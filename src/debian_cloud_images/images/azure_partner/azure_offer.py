import collections.abc
import copy
import logging
import typing

from .azure_sku import AzureSkus
from .info import AzurePartnerInfo


logger = logging.getLogger(__name__)


class AzureOffer:
    skus: AzureSkus

    _info: AzurePartnerInfo
    _name: str

    __api_data: typing.Any
    __api_etag: str

    def __init__(self, info: AzurePartnerInfo, name: str) -> None:
        self._info = info
        self._name = name

        self._api_get()

        self.skus = AzureSkus(self._info, self.__api_data['definition']['plans'])

    def __enter__(self) -> 'AzureOffer':
        self.__commited = False
        return self

    def __exit__(self, type, value, tb) -> None:
        if not self.__commited:
            logger.debug('Rolling back')
            self._rollback()
        del self.__commited

    def _rollback(self) -> None:
        for i in self.skus.values():
            try:
                i._rollback()
            except BaseException:
                logger.exception('Failed to rollback')

    def _api_get(self):
        offer_path = f'/api/publishers/{self._info.publisher}/offers/{self._name}'
        r = self._info.driver.request(offer_path)
        self.__api_data, self.__api_etag = r.parse_body(), r.headers.get('etag', '*')

    def _api_write(self, api_data):
        offer_path = f'/api/publishers/{self._info.publisher}/offers/{self._name}'
        r = self._info.driver.request(offer_path, method='PUT', data=api_data, headers={'If-Match': self.__api_etag})
        self.__api_data, self.__api_etag = r.parse_body(), r.headers.get('etag', '*')

    def api_update(self) -> typing.Any:
        api_data = copy.deepcopy(self.__api_data)
        self.skus.api_update(api_data['definition']['plans'])
        return api_data

    def commit(self) -> None:
        api_data_updated = self.api_update()
        self._api_write(api_data_updated)
        self.__commited = True


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
