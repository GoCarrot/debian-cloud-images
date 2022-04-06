import collections.abc
import http
import logging
import typing

from debian_cloud_images.utils.libcloud.storage.azure_arm import (
    AzureBlobsOAuth2StorageDriver,
    AzureResourceManagementStorageDriver,
)

logger = logging.getLogger(__name__)


class ImagesAzureStorageFolder:
    __name_resource_group: str
    __name_storage: str
    __name_folder: str
    __driver: AzureResourceManagementStorageDriver
    __driver_storage: AzureBlobsOAuth2StorageDriver

    def __init__(
            self,
            resource_group: str,
            storage: str,
            name: str,
            driver: AzureResourceManagementStorageDriver,
            driver_storage: AzureBlobsOAuth2StorageDriver = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_storage = storage
        self.__name_folder = name
        self.__driver = driver
        self.__driver_storage = driver_storage or driver.get_storage(storage, resource_group)

    @property
    def name(self) -> str:
        return self.__name_folder

    def create(self, exist_ok=True) -> None:
        r = self.__driver_storage.connection.request(
            self.name,
            method='PUT',
            params={
                'restype': 'container',
            },
        )
        if r.status == http.HTTPStatus.CREATED:
            pass
        elif r.status == http.HTTPStatus.CONFLICT and exist_ok:
            pass
        else:
            raise RuntimeError('Error creating container: {0.error} ({0.status})'.format(r))


class ImagesAzureStorageFolders(collections.abc.Mapping):
    __items: typing.Mapping[str, ImagesAzureStorageFolder]

    __name_resource_group: str
    __name_storage: str
    __driver: AzureResourceManagementStorageDriver
    __driver_storage: AzureBlobsOAuth2StorageDriver

    def __init__(
            self,
            resource_group: str,
            storage: str,
            driver: AzureResourceManagementStorageDriver,
            driver_storage: AzureBlobsOAuth2StorageDriver = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_storage = storage
        self.__driver = driver
        self.__driver_storage = driver_storage or driver.get_storage(storage, resource_group)
        raise NotImplementedError

    def __getitem__(self, name: str) -> ImagesAzureStorageFolder:
        return self.__items[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.__items)

    def __len__(self) -> int:
        return len(self.__items)
