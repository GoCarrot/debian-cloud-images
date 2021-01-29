from ..common.azure import AzureGenericOAuth2Connection


class AzureCloudpartnerOAuth2Connection(AzureGenericOAuth2Connection):
    """ OAuth 2 authenticated connection for Azure Cloud Partner interface """
    def __init__(self, *, tenant_id, client_id, client_secret):
        super().__init__(
            host='cloudpartner.azure.com',
            tenant_id=tenant_id,
            subscription_id=None,
            client_id=client_id,
            client_secret=client_secret,
            login_host='login.microsoftonline.com',
            login_resource='https://cloudpartner.azure.com',
        )

    def add_default_params(self, params):
        params.update({
            'api-version': '2017-10-31',
        })
        return params
