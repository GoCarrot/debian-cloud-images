# SPDX-License-Identifier: GPL-2.0-or-later

import unittest.mock

from debian_cloud_images.images.azure.computegallery import ImagesAzureComputegallery
from debian_cloud_images.images.azure.computegallery_image import ImagesAzureComputegalleryImage


class TestImagesAzureComputegalleryImage:
    def test_get(self, azure_conn, requests_mock) -> None:
        computegallery = unittest.mock.NonCallableMock(spec=ImagesAzureComputegallery)
        computegallery.path = '/BASE'

        # https://learn.microsoft.com/en-us/rest/api/compute/gallerie-images/get
        requests_mock.get(
            'https://host/BASE/images/image',
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        r = ImagesAzureComputegalleryImage(
            computegallery,
            'image',
            azure_conn,
        )

        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }
