# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.backend.azure.computeimage import AzureComputeimage
from debian_cloud_images.backend.azure.resourcegroup import AzureResourcegroup


class TestAzureComputeimage:
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
        resourcegroup = unittest.mock.NonCallableMock(spec=AzureResourcegroup)
        resourcegroup.client = client
        resourcegroup.path = 'BASE'

        r = AzureComputeimage(
            resourcegroup,
            'image',
        )

        assert r.path == 'BASE/providers/Microsoft.Compute/images/image'
        assert r.data() == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='GET', json=None, params={'api-version': r.api_version}),
        ])
