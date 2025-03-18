# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import httpx
import logging
import time

from dataclasses import dataclass
from typing import (
    cast,
    ClassVar,
    IO,
    Self,
)

from debian_cloud_images.utils.files import ChunkedFile
from debian_cloud_images.utils.typing import JSONObject

from . import (
    AzureVmArch,
    AzureVmGeneration,
)
from .base import AzureBase
from .resourcegroup import AzureResourcegroup


logger = logging.getLogger(__name__)


@dataclass
class AzureComputedisk(AzureBase[AzureResourcegroup]):
    api_version: ClassVar[str] = '2024-03-02'

    parent: AzureResourcegroup

    @property
    def path(self) -> str:
        return f'{self.parent.path}/providers/Microsoft.Compute/disks/{self.name}'

    @classmethod
    def create(
        cls,
        resourcegroup: AzureResourcegroup,
        name: str,
        *,
        wait: bool = True,
        arch: AzureVmArch,
        generation: AzureVmGeneration,
        location: str | None = None,
        size: int,
    ) -> Self:
        data: JSONObject = {
            'location': location or resourcegroup.location(),
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
        ret = cls(
            parent=resourcegroup,
            name=name,
        )
        ret._do_put(
            data=data,
            wait=wait,
        )
        return ret

    def _upload_access_begin(self) -> str:
        data: JSONObject = {
            'access': 'Write',
            'durationInSeconds': 3600,
            'fileFormat': 'VHD',
        }
        response = self._request(method='POST', subresource='beginGetAccess', data=data)

        if response.status_code == httpx.codes.ACCEPTED:
            monitor = response.headers['location']
            for _ in range(10):
                response = self.client.request(url=monitor, method='GET')
                if response.status_code == httpx.codes.OK:
                    response_data = response.json()
                    return cast(str, response_data['accessSAS'])
                elif response.status_code == httpx.codes.ACCEPTED:
                    time.sleep(1)
                else:
                    break

        raise NotImplementedError

    def _upload_access_end(self) -> None:
        response = self._request(method='POST', subresource='endGetAccess', data={})

        if response.status_code == httpx.codes.ACCEPTED:
            monitor = response.headers['location']
            for _ in range(30):
                response = self.client.request(url=monitor, method='GET')
                if response.status_code == httpx.codes.OK:
                    return
                elif response.status_code == httpx.codes.ACCEPTED:
                    time.sleep(1)
                else:
                    break

        raise NotImplementedError

    def _upload_chunk(self, url: str, chunk: ChunkedFile.ChunkData) -> None:
        """ Upload a single block up to 4MB to Azure storage """
        buf = chunk.read()
        logging.debug('uploading start=%s, size=%s', chunk.offset, chunk.size)

        headers: dict[str, str] = {
            'Content-Length': str(chunk.size),
            'Range': 'bytes={}-{}'.format(chunk.offset, chunk.offset + chunk.size - 1),
            'x-ms-page-write': 'update',
        }

        r = self.client.request(
            url=url,
            method='PUT',
            params={'comp': 'page'},
            headers=headers,
            content=buf,
        )
        if r.status_code != httpx.codes.CREATED:
            raise RuntimeError('Error uploading file block: {0.status_code}'.format(r))

    def upload(self, f: IO[bytes]) -> None:
        chunked = ChunkedFile(f, 4 * 1024 * 1024)

        if cast(str, self.properties()['diskState']).lower() not in ('readytoupload', 'activeupload'):
            raise RuntimeError('Image already uploaded')

        url = self._upload_access_begin()

        for chunk in chunked:
            if chunk.is_data:
                self._upload_chunk(url, chunk)

        self._upload_access_end()
