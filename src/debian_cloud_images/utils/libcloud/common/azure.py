import datetime
import subprocess
import json
import logging

from libcloud.common.azure_arm import AzureResourceManagementConnection


logger = logging.getLogger(__name__)


class AzureGenericOAuth2Connection(AzureResourceManagementConnection):
    def __init__(self, key=None, secret=None, secure=True, host=None, *,
                 client_id, client_secret, tenant_id, subscription_id, login_resource, **kw):
        super().__init__(key=client_id, secret=client_secret)
        self.host = host
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.login_resource = login_resource

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
