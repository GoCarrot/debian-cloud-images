import datetime
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
                'properties': {
                    'primaryEndpoints': {
                        'blob': 'https://storage',
                    },
                },
                'name': 'item',
            },
        )

        # https://docs.microsoft.com/en-us/rest/api/storagerp/storage-accounts/list-keys
        requests_mock.post(
            'https://management.azure.com/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Storage/storageAccounts/storage/listKeys?api-version=2019-04-01',
            json={
                'keys': [
                    {
                        'value': '',
                    },
                ],
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

    def test_query_sas(self, folder, requests_mock):
        url = folder.query_sas(
            start=datetime.date(2020, 1, 1),
            expiry=datetime.date(2020, 1, 1),
            permission='z',
        )

        # XXX: Untested string!
        assert url == 'sp=z&st=2020-01-01T00%3A00%3A00Z&se=2020-01-01T00%3A00%3A00Z&sv=2020-12-06&sr=c&sig=d4WH0Brk41kB13PB48H5V5vP6xDdAzEfI%2FRypd%2BXpow%3D'
