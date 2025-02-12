# SPDX-License-Identifier: GPL-2.0-or-later

import logging

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    ClassVar,
    Self,
)

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ImagesAzureResourcegroup:
    _api_version: ClassVar[str] = '2021-04-01'

    subscription: str
    name: str
    location: str = field(repr=False, compare=False)
    properties: dict[str, Any] = field(repr=False, compare=False)
    _conn: AzureGenericOAuth2Connection = field(repr=False, compare=False)

    @classmethod
    def _path(cls, subscription: str, name: str) -> str:
        return f'/subscriptions/{subscription}/resourceGroups/{name}'

    @property
    def path(self) -> str:
        return self._path(self.subscription, self.name)

    @classmethod
    def _request(
        cls, *,
        conn: AzureGenericOAuth2Connection,
        path: str,
        subresource: str | None = None,
        method: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        if subresource:
            path = f'{path}/{subresource}'
        return conn.request(path, method=method, data=data, params={'api-version': cls._api_version})

    @classmethod
    def get(cls, name: str, conn: AzureGenericOAuth2Connection) -> Self:
        subscription = conn.subscription_id
        path = cls._path(subscription, name)
        response = cls._request(conn=conn, path=path, method='GET')
        data = response.parse_body()
        return cls(
            subscription=subscription,
            name=data['name'],
            location=data['location'],
            properties=data['properties'],
            _conn=conn,
        )
