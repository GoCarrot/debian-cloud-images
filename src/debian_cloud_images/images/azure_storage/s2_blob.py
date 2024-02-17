# SPDX-License-Identifier: GPL-2.0-or-later

import collections.abc
import http
import logging
import typing
import urllib.parse

from libcloud.storage.drivers.azure_blobs import AzureBlobLease

from debian_cloud_images.utils.files import ChunkedFile
from debian_cloud_images.utils.libcloud.storage.azure_arm import (
    AzureBlobsOAuth2StorageDriver,
    AzureResourceManagementStorageDriver,
)
from typing import Optional


logger = logging.getLogger(__name__)


class ImagesAzureStorageBlob:
    __name_resource_group: str
    __name_storage: str
    __name_folder: str
    __name_blob: str
    __driver: AzureResourceManagementStorageDriver
    __driver_storage: AzureBlobsOAuth2StorageDriver

    def __init__(
            self,
            resource_group: str,
            storage: str,
            folder: str,
            name: str,
            driver: AzureResourceManagementStorageDriver,
            driver_storage: Optional[AzureBlobsOAuth2StorageDriver] = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_storage = storage
        self.__name_folder = folder
        self.__name_blob = name
        self.__driver = driver
        self.__driver_storage = driver_storage or driver.get_storage(storage, resource_group)

    @property
    def name(self) -> str:
        return self.__name_blob

    @property
    def path(self) -> str:
        return f'/{self.__name_folder}/{self.__name_blob}'

    @property
    def url(self) -> str:
        return urllib.parse.urljoin(f'https://{self.__driver_storage.connection.host}/', self.path)

    def __request(
            self,
            method: str,
            data: Optional[typing.Any] = None,
            headers: Optional[typing.Any] = None,
            params: Optional[typing.Any] = None,
    ) -> typing.Any:
        return self.__driver_storage.connection.request(self.path, method=method, data=data, headers=headers, params=params)

    def delete(self, notexist_ok=True) -> None:
        r = self.__request(method='DELETE')
        if r.status == http.HTTPStatus.ACCEPTED:
            pass
        elif r.status == http.HTTPStatus.NOT_FOUND and notexist_ok:
            pass
        else:
            raise RuntimeError('Error deleting blob: {0.error} ({0.status})'.format(r))

    def put(self, f: typing.BinaryIO) -> None:
        chunked = ChunkedFile(f, 4 * 1024 * 1024)

        with AzureBlobLease(self.__driver_storage, self.path, True) as lease:
            headers = {
                'x-ms-blob-type': 'PageBlob',
                'x-ms-blob-content-length': str(chunked.size),
            }
            lease.update_headers(headers)

            r = self.__request(
                method='PUT',
                headers=headers,
            )
            if r.status != http.HTTPStatus.CREATED:
                raise RuntimeError('Error creating file: {0.error} ({0.status})'.format(r))

            for chunk in chunked:
                if chunk.is_data:
                    self.put_chunk(lease, chunk)

    def put_chunk(self, lease, chunk):
        """ Upload a single block up to 4MB to Azure storage """
        buf = chunk.read()
        logging.debug('uploading start=%s, size=%s', chunk.offset, chunk.size)

        headers = {
            'Content-Length': chunk.size,
            'Range': 'bytes={}-{}'.format(chunk.offset, chunk.offset + chunk.size - 1),
            'x-ms-page-write': 'update',
        }
        lease.update_headers(headers)
        lease.renew()

        r = self.__request(
            method='PUT',
            params={'comp': 'page'},
            headers=headers,
            data=buf,
        )
        if r.status != http.HTTPStatus.CREATED:
            raise RuntimeError('Error uploading file block: {0.error} ({0.status})'.format(r))


class ImagesAzureStorageBlobs(collections.abc.Mapping):
    __items: typing.Mapping[str, ImagesAzureStorageBlob]

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
        raise NotImplementedError

    def __getitem__(self, name: str) -> ImagesAzureStorageBlob:
        return self.__items[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.__items)

    def __len__(self) -> int:
        return len(self.__items)
