# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.images.azure.computedisk import ImagesAzureComputedisk
from debian_cloud_images.images.azure.computegallery_image import ImagesAzureComputegalleryImage
from debian_cloud_images.images.azure.computegallery_image_version import ImagesAzureComputegalleryImageVersion


class TestImagesAzureComputegalleryImageVersion:
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
        elif method == 'PUT':
            ret.parse_body = unittest.mock.Mock(return_value={
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
            raise RuntimeError(path, method, kw)

        return ret

    def test_get(self, azure_conn) -> None:
        computegallery_image = unittest.mock.NonCallableMock(spec=ImagesAzureComputegalleryImage)
        computegallery_image.path = ''

        r = ImagesAzureComputegalleryImageVersion(
            computegallery_image,
            'version',
            azure_conn,
        )

        assert r.path == '/versions/version'
        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='GET', data=None, params={'api-version': r.api_version}),
        ])

    def test_create(self, azure_conn) -> None:
        computegallery_image = unittest.mock.NonCallableMock(spec=ImagesAzureComputegalleryImage)
        computegallery_image.path = ''

        computedisk = unittest.mock.NonCallableMock(spec=ImagesAzureComputedisk)
        computedisk.location = 'location'
        computedisk.path = ''

        r = ImagesAzureComputegalleryImageVersion.create(
            computegallery_image,
            'version',
            azure_conn,
            disk=computedisk,
        )

        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='PUT', data=unittest.mock.ANY, params={'api-version': r.api_version}),
        ])
