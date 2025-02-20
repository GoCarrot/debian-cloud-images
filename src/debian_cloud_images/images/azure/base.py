# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging
import time

from dataclasses import (
    dataclass,
    field,
    InitVar,
)
from typing import (
    Any,
    cast,
    ClassVar,
    Generic,
    TypeVar,
)

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.typing import JSONObject


Parent = TypeVar('Parent', bound='ImagesAzureBase')


logger = logging.getLogger(__name__)


@dataclass
class ImagesAzureBase(Generic[Parent]):
    api_version: ClassVar[str]

    parent: Parent
    name: str
    conn: AzureGenericOAuth2Connection = field(repr=False, compare=False)
    data: JSONObject = field(init=False, compare=False)
    _create_data: InitVar[JSONObject | None] = field(default=None, kw_only=True)
    _create_wait: InitVar[bool] = field(default=False, kw_only=True)

    def __post_init__(
        self,
        create_data: JSONObject | None,
        create_wait: bool,
    ) -> None:
        if create_data is not None:
            self._do_put(create_data)
            if create_wait:
                self._wait_state()
        else:
            self._do_get()

    @property
    def location(self) -> str:
        return cast(str, self.data['location'])

    @property
    def path(self) -> str:
        raise NotImplementedError

    @property
    def properties(self) -> JSONObject:
        return cast(JSONObject, self.data['properties'])

    def _request(
        self, *,
        subresource: str | None = None,
        method: str,
        data: JSONObject | None = None,
    ) -> Any:
        path = self.path
        if subresource:
            path = f'{path}/{subresource}'
        return self.conn.request(path, method=method, data=data, params={'api-version': self.api_version})  # type: ignore

    def _request_data(
        self, *,
        method: str,
        data: JSONObject | None = None,
    ) -> None:
        response = self._request(method=method, data=data)
        ret: JSONObject = response.parse_body()
        del ret['id']
        del ret['name']
        self.data = ret

    def _do_delete(self) -> None:
        self._request(method='DELETE')

    def _do_get(self) -> None:
        self._request_data(method='GET')

    def _do_put(self, data: JSONObject) -> None:
        self._request_data(method='PUT', data=data)

    def delete(self) -> None:
        self._do_delete()

    def update(self, data: JSONObject) -> None:
        self._do_put(data)

    def _wait_state(self, timeout: int = 1800, interval: int = 1) -> None:
        start_time = time.time()

        while time.time() - start_time < timeout:
            self._do_get()
            state = cast(str, self.properties['provisioningState']).lower()
            logging.debug('Privisioning state of resource: %s', state)

            if state == 'succeeded':
                return
            elif state in ('creating', 'updating'):
                time.sleep(interval)
                continue
            else:
                raise RuntimeError('Resource creation ended with unknown state: %s' % state)

        raise RuntimeError('Timeout while waiting for resource creation to succeed')
