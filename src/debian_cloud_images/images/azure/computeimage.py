# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import (
    ClassVar,
    Self,
)

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.typing import JSONObject

from .base import ImagesAzureBase
from .computedisk import ImagesAzureComputedisk
from .resourcegroup import ImagesAzureResourcegroup


logger = logging.getLogger(__name__)


@dataclass
class ImagesAzureComputeimage(ImagesAzureBase[ImagesAzureResourcegroup]):
    api_version: ClassVar[str] = '2021-11-01'

    @property
    def path(self) -> str:
        return f'{self.parent.path}/providers/Microsoft.Compute/images/{self.name}'

    @classmethod
    def create(
        cls,
        resourcegroup: ImagesAzureResourcegroup,
        name: str,
        conn: AzureGenericOAuth2Connection,
        *,
        wait: bool = True,
        disk: ImagesAzureComputedisk,
    ) -> Self:
        data: JSONObject = {
            'location': disk.location,
            'properties': {
                'hyperVGeneration': disk.properties['hyperVGeneration'],
                'storageProfile': {
                    'osDisk': {
                        'osType': 'Linux',
                        'managedDisk': {
                            'id': disk.path,
                        },
                        'osState': 'Generalized',
                    },
                },
            },
        }
        return cls(
            parent=resourcegroup,
            name=name,
            conn=conn,
            _create_data=data,
            _create_wait=wait,
        )
