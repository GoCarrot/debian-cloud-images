# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import (
    ClassVar,
    Self,
)

from debian_cloud_images.utils.typing import JSONObject

from .base import AzureBase
from .computedisk import AzureComputedisk
from .resourcegroup import AzureResourcegroup


logger = logging.getLogger(__name__)


@dataclass
class AzureComputeimage(AzureBase[AzureResourcegroup]):
    api_version: ClassVar[str] = '2021-11-01'

    @property
    def path(self) -> str:
        return f'{self.parent.path}/providers/Microsoft.Compute/images/{self.name}'

    @classmethod
    def create(
        cls,
        resourcegroup: AzureResourcegroup,
        name: str,
        *,
        wait: bool = True,
        disk: AzureComputedisk,
    ) -> Self:
        data: JSONObject = {
            'location': disk.location(),
            'properties': {
                'hyperVGeneration': disk.properties()['hyperVGeneration'],
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
        ret = cls(
            parent=resourcegroup,
            name=name,
        )
        ret._do_put(
            data=data,
            wait=wait,
        )
        return ret
