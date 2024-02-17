# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.images.azure_storage.s2_blob import (
    ImagesAzureStorageBlob,
)


class TestImagesAzureStorageBlob:
    @pytest.fixture
    def blob(self, azure_driver, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/storagerp/storage-accounts/get-properties#storageaccountgetproperties
        requests_mock.get(
            'https://management.azure.com/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Storage/storageAccounts/storage?api-version=2018-07-01',

            json={
                "properties": {
                    'primaryEndpoints': {
                        'blob': 'https://storage',
                    },
                },
                "name": "item",
            },
        )

        return ImagesAzureStorageBlob(
            'resource_group',
            'storage',
            'folder',
            'blob',
            azure_driver,
        )

    def test_delete(self, blob, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/storageservices/delete-blob
        requests_mock.delete(
            'https://storage/folder/blob',
            status_code=202,
        )

        blob.delete()

    def test_delete_error(self, blob, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/storageservices/delete-blob
        requests_mock.delete(
            'https://storage/folder/blob',
            status_code=500,
        )

        with pytest.raises(Exception):
            blob.delete()

    def test_delete_notexist_notok(self, blob, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/storageservices/delete-blob
        requests_mock.delete(
            'https://storage/folder/blob',
            status_code=404,
        )

        with pytest.raises(RuntimeError):
            blob.delete(False)

    def test_delete_notexist_ok(self, blob, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/storageservices/delete-blob
        requests_mock.delete(
            'https://storage/folder/blob',
            status_code=404,
        )

        blob.delete(True)

    def test_put(self, blob, requests_mock, tmp_path):
        # https://docs.microsoft.com/en-us/rest/api/storageservices/put-blob
        requests_mock.put(
            'https://storage/folder/blob',
            request_headers={
                'x-ms-lease-id': 'lease-id',
            },
            status_code=201,
        )

        # https://docs.microsoft.com/en-us/rest/api/storageservices/lease-blob
        requests_mock.put(
            'https://storage/folder/blob?comp=lease',
            headers={
                'x-ms-lease-id': 'lease-id',
            },
            status_code=201,
        )
        requests_mock.put(
            'https://storage/folder/blob?comp=lease',
            request_headers={
                'x-ms-lease-id': 'lease-id',
            },
            status_code=200,
        )

        # https://docs.microsoft.com/en-us/rest/api/storageservices/put-page
        requests_mock.put(
            'https://storage/folder/blob?comp=page',
            request_headers={
                'x-ms-lease-id': 'lease-id',
            },
            status_code=201,
        )

        with (tmp_path / 'blob').open('w+b') as f:
            f.write(b'1' * 4 * 1024 * 1024)
            f.seek(0)

            blob.put(f)
