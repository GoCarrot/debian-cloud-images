# SPDX-License-Identifier: GPL-2.0-or-later

import http
import logging
import typing

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from typing import Optional


logger = logging.getLogger(__name__)


class ImagesAzurePartnerlegacyOffer:
    __name_publisher: str
    __name_offer: str
    __conn: AzureGenericOAuth2Connection

    api_version = '2017-10-31'

    def __init__(
            self,
            publisher: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_publisher = publisher
        self.__name_offer = name
        self.__conn = conn

    @property
    def path(self) -> str:
        return f'/api/publishers/{self.__name_publisher}/offers/{self.__name_offer}'

    def __request(self, path: str, method: str, data: Optional[typing.Any] = None) -> typing.Any:
        return self.__conn.request(path, method=method, data=data, params={'api-version': self.api_version})

    def get(self, slot: Optional[str] = None) -> typing.Any:
        if slot:
            path = f'{self.path}/slot/{slot}'
        else:
            path = self.path
        response = self.__request(path=path, method='GET')
        return response.parse_body()

    def put(self, data: typing.Any) -> None:
        response = self.__request(path=self.path, method='PUT', data=data)
        if response.status != http.HTTPStatus.OK:
            raise RuntimeError('Failed')

    def control_golive(self) -> None:
        path = f'{self.path}/golive'
        self.__request(path=path, method='POST')

    def control_publish(self) -> None:
        path = f'{self.path}/publish'
        # E-mail address is actually ignored
        self.__request(path=path, method='POST', data={'metadata': {'notification-emails': 'jondoe@contoso.com'}})

    def op_cleanup(self, remove: typing.Callable[[str], bool]) -> set[str]:
        data = self.get()
        removed: set[str] = set()
        for plan in data['definition']['plans']:
            removed |= self.__op_cleanup_versions(plan['microsoft-azure-corevm.vmImagesPublicAzure'], remove)
            for generation in plan['diskGenerations']:
                removed |= self.__op_cleanup_versions(generation['microsoft-azure-corevm.vmImagesPublicAzure'], remove)
        if removed:
            self.put(data)
        return removed

    def __op_cleanup_versions(self, versions, remove: typing.Callable[[str], bool]) -> set[str]:
        removed: set[str] = set()
        for k in list(versions.keys()):
            if remove(k) is True:
                del versions[k]
                removed.add(k)
        return removed
