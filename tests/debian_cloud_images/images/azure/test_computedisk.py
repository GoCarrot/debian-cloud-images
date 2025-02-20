# SPDX-License-Identifier: GPL-2.0-or-later

import http

from debian_cloud_images.images.azure.computedisk import (
    ImagesAzureComputedisk,
    ImagesAzureComputediskArch,
    ImagesAzureComputediskGeneration,
)

from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup


class TestImagesAzureComputeimageImage:
    def test_create(self, azure_conn, requests_mock):
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

        # https://learn.microsoft.com/en-us/rest/api/compute/disks/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/disks/disk?api-version=2024-03-02',
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

        # https://learn.microsoft.com/en-us/rest/api/compute/disks/create-or-update
        requests_mock.put(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/disks/disk?api-version=2024-03-02',
            status_code=http.HTTPStatus.ACCEPTED,
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Updating',
                },
            },
        )

        group = ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        )

        disk = ImagesAzureComputedisk.create(
            group,
            'disk',
            conn=azure_conn,
            arch=ImagesAzureComputediskArch.amd64,
            generation=ImagesAzureComputediskGeneration.v2,
            location='location',
            size=10,
        )

        assert disk.properties == {
            'provisioningState': 'Succeeded',
        }

    def test_upload(self, azure_conn, requests_mock):
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

        # https://learn.microsoft.com/en-us/rest/api/compute/disks/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/disks/disk?api-version=2024-03-02',
            status_code=http.HTTPStatus.OK,
            json={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'diskState': 'ReadyToUpload',
                },
            },
        )

        # https://learn.microsoft.com/en-us/rest/api/compute/disks/grant-access
        requests_mock.post(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/disks/disk/beginGetAccess?api-version=2024-03-02',
            status_code=http.HTTPStatus.ACCEPTED,
            headers={
                'Location': 'https://host/beginGetAccess/monitor',
            },
        )

        requests_mock.get(
            'https://host/beginGetAccess/monitor',
            status_code=http.HTTPStatus.OK,
            json={
                'accessSAS': 'https://storage/',
            },
        )

        # https://learn.microsoft.com/en-us/rest/api/compute/disks/revoke-access
        requests_mock.post(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/disks/disk/endGetAccess?api-version=2024-03-02',
            status_code=http.HTTPStatus.ACCEPTED,
            headers={
                'Location': 'https://host/endGetAccess/monitor',
            },
        )

        requests_mock.get(
            'https://host/endGetAccess/monitor',
            status_code=http.HTTPStatus.OK,
        )

        requests_mock.put(
            'https://storage',
            status_code=http.HTTPStatus.CREATED,
        )

        group = ImagesAzureResourcegroup(
            'resource_group',
            azure_conn,
        )

        disk = ImagesAzureComputedisk(
            group,
            'disk',
            azure_conn,
        )

        with open(__file__, 'rb') as f:
            disk.upload(f)
