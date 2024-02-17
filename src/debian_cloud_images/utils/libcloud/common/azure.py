# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import subprocess
import json
import logging

from libcloud.common.azure_arm import AzureResourceManagementConnection
from libcloud.http import LibcloudConnection
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class LibcloudRetryConnection(LibcloudConnection):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        retry_strategy = Retry(
            total=3,
            status_forcelist={500, 502, 504},
            backoff_factor=1,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))


class AzureGenericOAuth2Connection(AzureResourceManagementConnection):
    conn_class = LibcloudRetryConnection

    def __init__(self, key=None, secret=None, secure=True, host=None, *,
                 client_id, client_secret, tenant_id, subscription_id, login_resource, **kw):
        super().__init__(key=client_id, secret=client_secret)
        self.host = host
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.login_resource = login_resource

        self.access_token = ''
        self.expires_on = -1

    def get_token_from_credentials(self):
        if self.user_id and self.key:
            return super().get_token_from_credentials()

        logger.debug('Trying to get auth via az account get-access-token')
        data = json.loads(subprocess.check_output((
            'az',
            'account',
            'get-access-token',
            self.subscription_id and f'--subscription={self.subscription_id}' or f'--tenant={self.tenant_id}',
            f'--resource={self.login_resource}',
            '--output=json',
        )))
        assert data['tokenType'] == 'Bearer'

        self.access_token = data['accessToken']
        self.expires_on = datetime.datetime.fromisoformat(data['expiresOn']).timestamp()
