# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.images.azure.computeimage import ImagesAzureComputeimage
from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup


class TestImagesAzureComputeimage:
    @pytest.fixture
    def azure_conn(self) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()
        ret.request = unittest.mock.Mock(side_effect=self.mock_request)
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
        resourcegroup = unittest.mock.NonCallableMock(spec=ImagesAzureResourcegroup)
        resourcegroup.path = ''

        r = ImagesAzureComputeimage(
            resourcegroup,
            'image',
            azure_conn,
        )

        assert r.path == '/providers/Microsoft.Compute/images/image'
        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='GET', data=None, params={'api-version': r.api_version}),
        ])
