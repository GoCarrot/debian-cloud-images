# SPDX-License-Identifier: GPL-2.0-or-later

import http

from debian_cloud_images.images.azure.resourcegroup import (
    ImagesAzureResourcegroup,
)


class TestImagesAzureResourcegroup:
    def test_get(self, azure_conn, requests_mock):
        # https://learn.microsoft.com/en-us/rest/api/resources/resource-groups/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group',
            status_code=http.HTTPStatus.OK,
            json={
                'name': 'resource_group',
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        r = ImagesAzureResourcegroup.get(
            'resource_group',
            azure_conn,
        )

        assert r.location == 'location'
        assert r.properties == {
            'provisioningState': 'Succeeded',
        }
