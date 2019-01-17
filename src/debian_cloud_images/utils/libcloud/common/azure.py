from libcloud.common.azure_arm import AzureResourceManagementConnection


class AzureGenericOAuth2Connection(AzureResourceManagementConnection):
    def __init__(self, key=None, secret=None, secure=True, host=None, *,
                 client_id, client_secret, tenant_id, login_resource, **kw):
        super().__init__(key=client_id, secret=client_secret)
        self.host = host
        self.tenant_id = tenant_id
        self.login_resource = login_resource
