# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.backend.azure.computedisk import AzureComputedisk
from debian_cloud_images.backend.azure.computegallery_image import AzureComputegalleryImage
from debian_cloud_images.backend.azure.computegallery_image_version import AzureComputegalleryImageVersion


class TestAzureComputegalleryImageVersion:
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
        elif method == 'PUT':
            ret.json = unittest.mock.Mock(return_value={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Creating',
                },
            })
        elif method == 'DELETE':
            pass
        else:
            raise RuntimeError(url, method, kw)

        return ret

    def test_get(self, client) -> None:
        computegallery_image = unittest.mock.NonCallableMock(spec=AzureComputegalleryImage)
        computegallery_image.client = client
        computegallery_image.path = 'BASE'

        r = AzureComputegalleryImageVersion(
            computegallery_image,
            'version',
        )

        assert r.path == 'BASE/versions/version'
        assert r.data() == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='GET', json=None, params={'api-version': r.api_version}),
        ])

    def test_create(self, client) -> None:
        computegallery_image = unittest.mock.NonCallableMock(spec=AzureComputegalleryImage)
        computegallery_image.client = client
        computegallery_image.path = 'BASE'

        computedisk = unittest.mock.NonCallableMock(spec=AzureComputedisk)
        computedisk.location = unittest.mock.Mock(return_value='location')
        computedisk.path = 'DISK'

        r = AzureComputegalleryImageVersion.create(
            computegallery_image,
            'version',
            disk=computedisk,
        )

        assert r.data() == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='PUT', json=unittest.mock.ANY, params={'api-version': r.api_version}),
        ])
