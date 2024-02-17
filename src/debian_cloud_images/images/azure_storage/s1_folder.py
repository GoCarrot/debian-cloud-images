# SPDX-License-Identifier: GPL-2.0-or-later

import base64
import datetime
import collections.abc
import email.utils
import hashlib
import hmac
import http
import logging
import typing
import urllib.parse

from debian_cloud_images.utils.libcloud.storage.azure_arm import (
    AzureBlobsOAuth2StorageDriver,
    AzureResourceManagementStorageDriver,
)
from typing import Optional

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
            driver_storage: Optional[AzureBlobsOAuth2StorageDriver] = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_storage = storage
        self.__name_folder = name
        self.__driver = driver
        self.__driver_storage = driver_storage or driver.get_storage(storage, resource_group)

    @property
    def name(self) -> str:
        return self.__name_folder

    @property
    def path(self) -> str:
        return f'/{self.__name_folder}'

    def query_sas(
            self,
            start: datetime.date,
            expiry: datetime.date,
            permission: str = 'r',
    ) -> str:
        query: dict[str, str] = {
            'sp': permission,
            'st': start.strftime('%Y-%m-%dT00:00:00Z'),
            'se': expiry.strftime('%Y-%m-%dT00:00:00Z'),
            'sv': '2020-12-06',
            'sr': 'c',
        }

        # https://docs.microsoft.com/en-us/rest/api/storageservices/create-service-sas#version-2020-12-06-and-later
        tosign = (
            query['sp'],  # signedPermissions
            query['st'],  # signedStart
            query['se'],  # signedExpiry
            f'/blob/{self.__name_storage}/{self.__name_folder}',  # canonicalizedResource
            '',  # signedIdentifier
            '',  # signedIP
            '',  # signedProtocol
            query['sv'],  # signedVersion
            query['sr'],  # signedResource
            '',  # signedSnapshotTime
            '',  # signedEncryptionScope
            '',  # rscc
            '',  # rscd
            '',  # rsce
            '',  # rscl
            '',  # rsct
        )

        storage_secret = self.__driver.get_storagekeys(
            resource_group=self.__name_resource_group,
            name=self.__name_storage,
        )[0]

        key = base64.b64decode(storage_secret)
        signed_hmac_sha256 = hmac.HMAC(key, '\n'.join(tosign).encode('ascii'), hashlib.sha256)
        query['sig'] = base64.b64encode(signed_hmac_sha256.digest()).decode('ascii')

        return urllib.parse.urlencode(query)

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

    def op_cleanup(self, remove: typing.Callable[[datetime.datetime], bool]) -> set[str]:
        container = self.__driver_storage.get_container(self.name)
        removed = set()
        for obj in self.__driver_storage.iterate_container_objects(container):
            last_modified = email.utils.parsedate_to_datetime(obj.extra['last_modified'])
            if remove(last_modified):
                self.__driver_storage.delete_object(obj)
                removed.add(obj.name)
        return removed


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
            driver_storage: Optional[AzureBlobsOAuth2StorageDriver] = None,
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
