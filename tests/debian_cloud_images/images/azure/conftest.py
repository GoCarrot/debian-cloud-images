# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


@pytest.fixture
def azure_conn(requests_mock):
    requests_mock.post(
        'https://login.microsoftonline.com/tenant/oauth2/token',
        json={
            'access_key': 'access_key',
            'access_token': 'access_token',
            'expires_on': 0,
        },
    )

    return AzureGenericOAuth2Connection(
        key='key',
        secret='secret',
        host='host',
        client_id='client',
        client_secret='secret',
        tenant_id='tenant',
        subscription_id='subscription',
        login_resource='login',
    )
