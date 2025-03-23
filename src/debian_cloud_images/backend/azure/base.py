# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import httpx
import logging
import time
import urllib.parse

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    cast,
    ClassVar,
    Generic,
    TypeVar,
)

from debian_cloud_images.utils.typing import JSONObject


Parent = TypeVar('Parent', bound='AzureBaseClient')


logger = logging.getLogger(__name__)


@dataclass
class AzureBaseClient(Generic[Parent]):
    parent: Parent

    @property
    def client(self) -> httpx.Client:
        return self.parent.client


@dataclass
class AzureBase(AzureBaseClient[Parent]):
    api_version: ClassVar[str]

    name: str
    _data: JSONObject | None = field(default=None, init=False, compare=False)

    def data(self) -> JSONObject:
        if self._data is None:
            return self._do_get()
        return self._data

    def location(self) -> str:
        return cast(str, self.data()['location'])

    @property
    def path(self) -> str:
        raise NotImplementedError

    def properties(self) -> JSONObject:
        return cast(JSONObject, self.data()['properties'])

    def url(self, subresource: str | None = None) -> str:
        path = self.path
        if subresource:
            path = f'{path}/{subresource}'
        return urllib.parse.urljoin('https://management.azure.com', path)

    def _request(
        self, *,
        subresource: str | None = None,
        method: str,
        data: JSONObject | None = None,
    ) -> httpx.Response:
        url = self.url(subresource)
        resp = self.client.request(url=url, method=method, json=data, params={'api-version': self.api_version})
        resp.raise_for_status()
        return resp

    def _request_data(
        self, *,
        method: str,
        data: JSONObject | None = None,
    ) -> JSONObject:
        resp = self._request(method=method, data=data)
        if not resp.headers['content-type'].startswith('application/json'):
            raise RuntimeError
        ret = resp.json()
        del ret['id']
        ret.pop('name', None)
        self._data = ret
        return ret

    def _do_delete(self) -> None:
        self._request(method='DELETE')

    def _do_get(self) -> JSONObject:
        return self._request_data(method='GET')

    def _do_put(self, data: JSONObject, wait: bool = False) -> JSONObject:
        ret = self._request_data(method='PUT', data=data)
        if wait:
            self._wait_state()
        return ret

    def delete(self) -> None:
        self._do_delete()

    def update(self, data: JSONObject) -> None:
        self._do_put(data)

    def _wait_state(self, timeout: int = 1800, interval: int = 1) -> None:
        start_time = time.time()

        while time.time() - start_time < timeout:
            state = cast(str, self._do_get()['properties']['provisioningState']).lower()
            logging.debug('Privisioning state of resource: %s', state)

            if state == 'succeeded':
                return
            elif state in ('creating', 'updating'):
                time.sleep(interval)
                continue
            else:
                raise RuntimeError('Resource creation ended with unknown state: %s' % state)

        raise RuntimeError('Timeout while waiting for resource creation to succeed')
