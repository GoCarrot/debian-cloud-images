# SPDX-License-Identifier: GPL-2.0-or-later

import httpx
import json
import logging
import subprocess
import time

from dataclasses import (
    dataclass,
    field,
)
from typing import Generator


logger = logging.getLogger(__name__)


@dataclass
class AzureAuthScope:
    scope: str
    subscription: str
    access_token: str = field(init=False, repr=False)
    expires_on: int = field(init=False, default=0)


@dataclass
class AzureAuth(httpx.Auth):
    scopes: dict[tuple[str, ...], AzureAuthScope] = field(init=False, default_factory=dict)

    def get_client(self) -> httpx.Client:
        return httpx.Client(auth=self)

    def _get(self, request: httpx.Request) -> AzureAuthScope | None:
        host = request.url.host
        path_list = request.url.path.split('/', 4)[1:]
        if host == 'management.azure.com' and path_list[0] == 'subscriptions':
            key = ('https://management.core.windows.net/', path_list[1])
        else:
            return None

        if key in self.scopes:
            return self.scopes[key]
        return self.scopes.setdefault(key, AzureAuthScope(*key))

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response]:
        scope = self._get(request)
        if scope:
            if scope.expires_on <= (time.time() + 60):
                yield from self.update_token(scope)
            request.headers['Authorization'] = f'Bearer {scope.access_token}'
        yield request

    def update_token(self, scope: AzureAuthScope) -> Generator[httpx.Request, httpx.Response]:
        yield from []
        logger.debug('trying to authenticate via azure-cli')
        data = json.loads(subprocess.check_output((
            'az',
            'account',
            'get-access-token',
            f'--scope={scope.scope}',
            f'--subscription={scope.subscription}',
            '--output=json',
        )))
        scope.access_token = data['accessToken']
        scope.expires_on = int(data['expires_on'])


@dataclass
class AzureAuthServiceAccount(AzureAuth):
    tenant: str
    client_id: str
    client_secret: str = field(repr=False)

    def update_token(self, scope: AzureAuthScope) -> Generator[httpx.Request, httpx.Response]:
        logger.debug(f'trying to authenticate via service account {self.client_id}')
        request = httpx.Request('POST', f'https://login.microsoftonline.com/{self.tenant}/oauth2/token', data={
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': scope.scope,
        })
        response = yield request
        response.raise_for_status()
        response.read()
        data = response.json()
        scope.access_token = data['access_token']
        scope.expires_on = int(data['expires_on'])
