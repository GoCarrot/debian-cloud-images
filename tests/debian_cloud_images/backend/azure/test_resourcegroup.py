# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.backend.azure.resourcegroup import AzureResourcegroup
from debian_cloud_images.backend.azure.subscription import AzureSubscription


class TestAzureResourcegroup:
    @pytest.fixture
    def client(self) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()
        ret.request = unittest.mock.Mock(side_effect=self.mock_request)
        return ret

    def mock_request(self, *, url, method, **kw) -> unittest.mock.Mock:
        ret = unittest.mock.Mock()
        ret.headers = {
            'content-type': 'application/json',
        }

        if method == 'GET':
            ret.json = unittest.mock.Mock(return_value={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            })
        elif method == 'DELETE':
            pass
        else:
            raise RuntimeError(url, method, kw)

        return ret

    def test_get(self, client) -> None:
        subscription = unittest.mock.NonCallableMock(spec=AzureSubscription)
        subscription.client = client
        subscription.path = 'BASE'

        r = AzureResourcegroup(
            subscription,
            'resource_group',
        )

        assert r.path == 'BASE/resourceGroups/resource_group'
        assert r.data() == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='GET', json=None, params={'api-version': r.api_version}),
        ])

    def test_delete(self, client):
        subscription = unittest.mock.NonCallableMock(spec=AzureSubscription)
        subscription.client = client
        subscription.path = 'BASE'

        r = AzureResourcegroup(
            subscription,
            'resource_group',
        )
        r.delete()

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='DELETE', json=None, params={'api-version': r.api_version}),
        ])
