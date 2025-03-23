# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.backend.azure.subscription import AzureSubscription


class TestAzureSubscription:
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
            })
        else:
            raise RuntimeError(url, method, kw)

        return ret

    def test_get(self, client) -> None:
        r = AzureSubscription(
            client,
            'subscription',
        )

        assert r.path == '/subscriptions/subscription'
        assert r.data() == {}

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='GET', json=None, params={'api-version': r.api_version}),
        ])
