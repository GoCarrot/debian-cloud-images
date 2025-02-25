# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup


class TestImagesAzureResourcegroup:
    @pytest.fixture
    def azure_conn(self) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()
        ret.request = unittest.mock.Mock(side_effect=self.mock_request)
        ret.subscription_id = 'subscription'
        return ret

    def mock_request(self, path, *, method, **kw) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()

        if method == 'GET':
            ret.parse_body = unittest.mock.Mock(return_value={
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
            raise RuntimeError(path, method, kw)

        return ret

    def test_get(self, azure_conn):
        r = ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        )

        assert r.path == '/subscriptions/subscription/resourceGroups/resource_group'
        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='GET', data=None, params={'api-version': r.api_version}),
        ])

    def test_delete(self, azure_conn):
        r = ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        )
        r.delete()

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='DELETE', data=None, params={'api-version': r.api_version}),
        ])
