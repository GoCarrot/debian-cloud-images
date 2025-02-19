# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import enum
import http
import logging
import time
import urllib.parse

from dataclasses import dataclass
from typing import (
    cast,
    ClassVar,
    IO,
    Self,
)

from libcloud.common.base import Connection

from debian_cloud_images.utils.files import ChunkedFile
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.typing import JSONObject

from .base import ImagesAzureBase
from .resourcegroup import ImagesAzureResourcegroup


logger = logging.getLogger(__name__)


class ImagesAzureComputediskArch(enum.Enum):
    amd64 = 'x64'
    arm64 = 'arm64'


class ImagesAzureComputediskGeneration(enum.Enum):
    v1 = 'V1'
    v2 = 'V2'


@dataclass
class ImagesAzureComputedisk(ImagesAzureBase[ImagesAzureResourcegroup]):
    api_version: ClassVar[str] = '2024-03-02'

    parent: ImagesAzureResourcegroup

    @property
    def path(self) -> str:
        return f'{self.parent.path}/providers/Microsoft.Compute/disks/{self.name}'

    @classmethod
    def create(
        cls,
        resourcegroup: ImagesAzureResourcegroup,
        name: str,
        conn: AzureGenericOAuth2Connection,
        *,
        wait: bool = True,
        arch: ImagesAzureComputediskArch,
        generation: ImagesAzureComputediskGeneration,
        location: str | None = None,
        size: int,
    ) -> Self:
        data: JSONObject = {
            'location': location or resourcegroup.location,
            'properties': {
                'creationData': {
                    'createOption': 'Upload',
                    'uploadSizeBytes': size,
                },
                'hyperVGeneration': generation.value,
                'osType': 'Linux',
                'supportedCapabilities': {
                    'acceleratedNetwork': True,
                    'architecture': arch.value,
                    'diskControllerTypes': 'NVME, SCSI',
                },
            },
            'sku': {
                'name': 'StandardSSD_LRS',
            },
        }
        return cls(
            parent=resourcegroup,
            name=name,
            conn=conn,
            _create_data=data,
            _create_wait=wait,
        )

    def _upload_access_begin(self) -> str:
        data: JSONObject = {
            'access': 'Write',
            'durationInSeconds': 3600,
            'fileFormat': 'VHD',
        }
        response = self._request(method='POST', subresource='beginGetAccess', data=data)

        if response.status == http.HTTPStatus.ACCEPTED:
            monitor = urllib.parse.urlsplit(response.headers['location'])
            for _ in range(10):
                response = self.conn.request(f'{monitor.path}?{monitor.query}', method='GET')  # type: ignore
                if response.status == http.HTTPStatus.OK:
                    rdata = response.parse_body()
                    return cast(str, rdata['accessSAS'])
                elif response.status == http.HTTPStatus.ACCEPTED:
                    time.sleep(1)
                else:
                    break

        raise NotImplementedError

    def _upload_access_end(self) -> None:
        response = self._request(method='POST', subresource='endGetAccess', data={})

        if response.status == http.HTTPStatus.ACCEPTED:
            monitor = urllib.parse.urlsplit(response.headers['location'])
            for _ in range(30):
                response = self.conn.request(f'{monitor.path}?{monitor.query}', method='GET')  # type: ignore
                if response.status == http.HTTPStatus.OK:
                    return
                elif response.status == http.HTTPStatus.ACCEPTED:
                    time.sleep(1)
                else:
                    break

        raise NotImplementedError

    def _upload_chunk(self, conn: Connection, path: str, chunk: ChunkedFile.ChunkData) -> None:
        """ Upload a single block up to 4MB to Azure storage """
        buf = chunk.read()
        logging.debug('uploading start=%s, size=%s', chunk.offset, chunk.size)

        headers = {
            'Content-Length': chunk.size,
            'Range': 'bytes={}-{}'.format(chunk.offset, chunk.offset + chunk.size - 1),
            'x-ms-page-write': 'update',
        }

        r = conn.request(
            path,
            method='PUT',
            params={'comp': 'page'},
            headers=headers,
            data=buf,
        )  # type: ignore
        if r.status != http.HTTPStatus.CREATED:
            raise RuntimeError('Error uploading file block: {0.error} ({0.status})'.format(r))

    def upload(self, f: IO[bytes]) -> None:
        chunked = ChunkedFile(f, 4 * 1024 * 1024)

        if cast(str, self.properties['diskState']).lower() not in ('readytoupload', 'activeupload'):
            raise RuntimeError('Image already uploaded')

        url = urllib.parse.urlsplit(self._upload_access_begin())
        conn = Connection(
            host=url.netloc,
        )  # type: ignore

        for chunk in chunked:
            if chunk.is_data:
                self._upload_chunk(conn, f'{url.path}?{url.query}', chunk)

        self._upload_access_end()
