# SPDX-License-Identifier: GPL-2.0-or-later

import unittest.mock

from debian_cloud_images.images.azure.computegallery import ImagesAzureComputegallery
from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup


class TestImagesAzureComputegallery:
    def test_get(self, azure_conn, requests_mock) -> None:
        resourcegroup = unittest.mock.NonCallableMock(spec=ImagesAzureResourcegroup)
        resourcegroup.path = '/BASE'

        # https://learn.microsoft.com/en-us/rest/api/compute/galleries/get
        requests_mock.get(
            'https://host/BASE/providers/Microsoft.Compute/galleries/gallery',
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        r = ImagesAzureComputegallery(
            resourcegroup,
            'gallery',
            azure_conn,
        )

        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }
