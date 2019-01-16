from libcloud.compute.drivers.azure_arm import AzureNodeDriver

from ..common.azure import AzureGenericOAuth2Connection


class ExAzureNodeDriver(AzureNodeDriver):
    connectionCls = AzureGenericOAuth2Connection

    def __init__(self, *, client_id, client_secret, subscription_id, tenant_id):
        self.client_id = client_id
        self.client_secret = client_secret

        super().__init__(key='', secret='', tenant_id=tenant_id, subscription_id=subscription_id)

    def _ex_connection_class_kwargs(self):
        ret = super()._ex_connection_class_kwargs()
        ret.update({
            'host': 'management.azure.com',
            'login_resource': 'https://management.core.windows.net/',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'tenant_id': self.tenant_id,
        })
        return ret

    def ex_create_computeimage(self, name, ex_resource_group, location, ex_blob):
        action = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/images/{}'.format(
            self.subscription_id,
            ex_resource_group,
            name,
        )

        data = {
            'location': location,
            'properties': {
                'storageProfile': {
                    'osDisk': {
                        'osType': 'Linux',
                        'blobUri': ex_blob,
                        'osState': 'Generalized',
                    }
                }
            }
        }

        self.connection.request(action, data=data, method='PUT', params={'api-version': '2018-06-01'})
