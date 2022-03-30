import pytest

from debian_cloud_images.images.azure_storage.s1_folder import (
    ImagesAzureStorageFolder,
)


class TestImagesAzureStorageFolder:
    @pytest.fixture
    def folder(self, azure_driver, requests_mock):
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

        return ImagesAzureStorageFolder(
            'resource_group',
            'storage',
            'folder',
            azure_driver,
        )

    def test_create(self, folder, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/storageservices/create-container
        requests_mock.put(
            'https://storage/folder?restype=container',
            status_code=201,
        )

        folder.create()
