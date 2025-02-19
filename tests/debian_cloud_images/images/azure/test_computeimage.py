# SPDX-License-Identifier: GPL-2.0-or-later

import http

from debian_cloud_images.images.azure.computeimage import (
    ImagesAzureComputeimage,
)

from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup


class TestImagesAzureComputeimage:
    def test_get(self, azure_conn, requests_mock):
        # https://learn.microsoft.com/en-us/rest/api/resources/resource-groups/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group',
            status_code=http.HTTPStatus.OK,
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        # https://docs.microsoft.com/en-us/rest/api/compute/images/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/images/image',
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        group = ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        )

        r = ImagesAzureComputeimage(
            group,
            'image',
            azure_conn,
        )

        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }
