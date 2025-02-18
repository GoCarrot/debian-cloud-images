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
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Succeeded',
                },
            },
        )

        r = ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        )

        assert r.data == {
            'location': 'location',
            'properties': {
                'provisioningState': 'Succeeded',
            },
        }

    def test_delete(self, azure_conn, requests_mock):
        # https://learn.microsoft.com/en-us/rest/api/resources/resource-groups/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group',
            status_code=http.HTTPStatus.OK,
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {},
            },
        )

        requests_mock.delete(
            'https://host/subscriptions/subscription/resourceGroups/resource_group',
            status_code=http.HTTPStatus.OK,
        )

        ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        ).delete()
