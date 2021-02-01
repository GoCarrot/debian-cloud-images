import time
import typing

from libcloud.common.azure import AzureResponse
from libcloud.storage.drivers.azure_blobs import AzureBlobsStorageDriver

from ..common.azure import AzureGenericOAuth2Connection


class AzureStorageOAuth2Connection(AzureGenericOAuth2Connection):
    responseCls: typing.Type = AzureResponse

    def add_default_headers(self, headers):
        headers['Authorization'] = "Bearer %s" % self.access_token
        headers['x-ms-date'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        headers['x-ms-version'] = '2017-11-09'
        return headers

    def encode_data(self, data):
        return data


class AzureBlobsOAuth2StorageDriver(AzureBlobsStorageDriver):
    name = 'Microsoft Azure (blobs with OAuth2)'
    connectionCls: typing.Type = AzureStorageOAuth2Connection

    def __init__(self, key, *, client_id, client_secret, tenant_id, subscription_id, host=None, extra=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.extra = extra or {}

        super().__init__(key=key, secret='', host=host)

    def _ex_connection_class_kwargs(self):
        ret = super()._ex_connection_class_kwargs()
        ret.update({
            'login_resource': 'https://storage.azure.com/',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'tenant_id': self.tenant_id,
            'subscription_id': self.subscription_id,
        })
        return ret
