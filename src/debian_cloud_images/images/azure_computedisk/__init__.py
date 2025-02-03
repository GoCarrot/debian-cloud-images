# SPDX-License-Identifier: GPL-2.0-or-later

import dataclasses
import enum
import http
import logging
import time
import typing
import urllib.parse

from libcloud.common.base import Connection
from typing import Optional

from debian_cloud_images.utils.files import ChunkedFile
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzureComputediskArch(enum.StrEnum):
    amd64 = 'X64'
    arm64 = 'Arm64'


@dataclasses.dataclass
class ImagesAzureComputedisk:
    api_version: typing.ClassVar[str] = '2024-03-02'

    name_resource_group: str
    name: str
    conn: AzureGenericOAuth2Connection

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.conn.subscription_id}/resourceGroups/{self.name_resource_group}/providers/Microsoft.Compute/disks/{self.name}'

    def __request(self, *, subresource: Optional[str] = None, method: str, data: Optional[typing.Any] = None) -> typing.Any:
        path = self.path
        if subresource:
            path = f'{path}/{subresource}'
        return self.conn.request(path, method=method, data=data, params={'api-version': self.api_version})

    def create(
            self,
            *,
            arch: ImagesAzureComputediskArch,
            generation: int,
            location: str,
            size: int,
    ) -> typing.Any:
        data = {
            'location': location,
            'properties': {
                'creationData': {
                    'createOption': 'Upload',
                    'uploadSizeBytes': size,
                },
                'hyperVGeneration': f'V{generation}',
                'osType': 'Linux',
                'supportedCapabilities': {
                    'acceleratedNetwork': True,
                    'architecture': str(arch),
                    'diskControllerTypes': 'NVME, SCSI',
                },
            },
            'sku': {
                'name': 'StandardSSD_LRS',
            },
        }
        response = self.__request(method='PUT', data=data)
        data = response.parse_body()
        return self._wait_create()

    def delete(self) -> None:
        self.__request(method='DELETE')

    def get(self) -> dict[str, typing.Any]:
        response = self.__request(method='GET')
        data = response.parse_body()
        return data['properties']

    def _upload_access_begin(self) -> str:
        data = {
            'access': 'Write',
            'durationInSeconds': 3600,
            'fileFormat': 'VHD',
        }
        response = self.__request(method='POST', subresource='beginGetAccess', data=data)

        if response.status == http.HTTPStatus.ACCEPTED:
            monitor = urllib.parse.urlsplit(response.headers['location'])
            for _ in range(10):
                response = self.conn.request(f'{monitor.path}?{monitor.query}', method='GET')
                if response.status == http.HTTPStatus.OK:
                    rdata = response.parse_body()
                    return rdata['accessSAS']
                elif response.status == http.HTTPStatus.ACCEPTED:
                    time.sleep(1)
                else:
                    break

        raise NotImplementedError

    def _upload_access_end(self) -> None:
        response = self.__request(method='POST', subresource='endGetAccess', data={})

        if response.status == http.HTTPStatus.ACCEPTED:
            monitor = urllib.parse.urlsplit(response.headers['location'])
            for _ in range(30):
                response = self.conn.request(f'{monitor.path}?{monitor.query}', method='GET')
                if response.status == http.HTTPStatus.OK:
                    return
                elif response.status == http.HTTPStatus.ACCEPTED:
                    time.sleep(1)
                else:
                    break

        raise NotImplementedError

    def _upload_chunk(self, conn, path, chunk):
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
        )
        if r.status != http.HTTPStatus.CREATED:
            raise RuntimeError('Error uploading file block: {0.error} ({0.status})'.format(r))

    def upload(self, f: typing.IO[bytes]) -> None:
        chunked = ChunkedFile(f, 4 * 1024 * 1024)

        if self.get()['diskState'].lower() not in ('readytoupload', 'activeupload'):
            raise RuntimeError('Image already uploaded')

        url = urllib.parse.urlsplit(self._upload_access_begin())
        conn = Connection(
            host=url.netloc,
        )

        for chunk in chunked:
            if chunk.is_data:
                self._upload_chunk(conn, f'{url.path}?{url.query}', chunk)

        self._upload_access_end()

    def _wait_create(self, timeout=1800, interval=1):
        start_time = time.time()

        while time.time() - start_time < timeout:
            properties = self.get()
            state = properties['provisioningState'].lower()
            logging.debug('Privisioning state of image: %s', state)

            if state == 'succeeded':
                return properties
            elif state in ('creating', 'updating'):
                time.sleep(interval)
                continue
            else:
                raise RuntimeError('Image creation ended with unknown state: %s' % state)

        raise RuntimeError('Timeout while waiting for image creation to succeed')
