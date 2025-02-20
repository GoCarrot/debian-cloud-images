# SPDX-License-Identifier: GPL-2.0-or-later

import unittest.mock

from debian_cloud_images.images.azure.computedisk import ImagesAzureComputedisk
from debian_cloud_images.images.azure.computegallery_image import ImagesAzureComputegalleryImage
from debian_cloud_images.images.azure.computegallery_image_version import ImagesAzureComputegalleryImageVersion


class TestImagesAzureComputegalleryImageVersion:
    def test_get(self, azure_conn, requests_mock) -> None:
        computegallery_image = unittest.mock.NonCallableMock(spec=ImagesAzureComputegalleryImage)
        computegallery_image.path = '/BASE'

        # https://learn.microsoft.com/en-us/rest/api/compute/gallerie-image-versions/get
        requests_mock.get(
            'https://host/BASE/versions/version',
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        r = ImagesAzureComputegalleryImageVersion(
            computegallery_image,
            'version',
            azure_conn,
        )

        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

    def test_create(self, azure_conn, requests_mock) -> None:
        computegallery_image = unittest.mock.NonCallableMock(spec=ImagesAzureComputegalleryImage)
        computegallery_image.path = '/BASE'

        computedisk = unittest.mock.NonCallableMock(spec=ImagesAzureComputedisk)
        computedisk.location = 'location'
        computedisk.path = '/BASE'

        # https://learn.microsoft.com/en-us/rest/api/compute/gallerie-image-versions/create-or-update
        requests_mock.put(
            'https://host/BASE/versions/version',
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Creating',
                },
            },
        )

        # https://learn.microsoft.com/en-us/rest/api/compute/gallerie-image-versions/get
        requests_mock.get(
            'https://host/BASE/versions/version',
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

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
