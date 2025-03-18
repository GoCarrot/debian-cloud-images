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
from .computegallery_image import AzureComputegalleryImage


logger = logging.getLogger(__name__)


@dataclass
class AzureComputegalleryImageVersion(AzureBase[AzureComputegalleryImage]):
    api_version: ClassVar[str] = '2024-03-03'

    @property
    def path(self) -> str:
        return f'{self.parent.path}/versions/{self.name}'

    @classmethod
    def create(
        cls,
        computegallery_image: AzureComputegalleryImage,
        # TODO: take as object
        name: str,
        *,
        wait: bool = True,
        disk: AzureComputedisk,
    ) -> Self:
        data: JSONObject = {
            'location': disk.location(),
            'properties': {
                'publishingProfile': {
                },
                'storageProfile': {
                    'osDiskImage': {
                        'source': {
                            'id': disk.path,
                        },
                    },
                },
            },
        }
        ret = cls(
            parent=computegallery_image,
            name=name,
        )
        ret._do_put(
            data=data,
            wait=wait,
        )
        return ret
