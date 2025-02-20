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
from .computegallery_image import ImagesAzureComputegalleryImage


logger = logging.getLogger(__name__)


@dataclass
class ImagesAzureComputegalleryImageVersion(ImagesAzureBase[ImagesAzureComputegalleryImage]):
    api_version: ClassVar[str] = '2024-03-03'

    @property
    def path(self) -> str:
        return f'{self.parent.path}/versions/{self.name}'

    @classmethod
    def create(
        cls,
        computegallery_image: ImagesAzureComputegalleryImage,
        # TODO: take as object
        name: str,
        conn: AzureGenericOAuth2Connection,
        *,
        wait: bool = True,
        disk: ImagesAzureComputedisk,
    ) -> Self:
        data: JSONObject = {
            'location': disk.location,
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
        return cls(
            parent=computegallery_image,
            name=name,
            conn=conn,
            _create_data=data,
            _create_wait=wait,
        )
