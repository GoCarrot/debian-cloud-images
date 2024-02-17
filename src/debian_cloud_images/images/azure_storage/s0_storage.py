# SPDX-License-Identifier: GPL-2.0-or-later

import logging

from debian_cloud_images.utils.libcloud.storage.azure_arm import (
    AzureBlobsOAuth2StorageDriver,
    AzureResourceManagementStorageDriver,
)
from typing import Optional


logger = logging.getLogger(__name__)


class AzureStorage:
    __name_resource_group: str
    __name_storage: str
    __driver: AzureResourceManagementStorageDriver
    __driver_storage: AzureBlobsOAuth2StorageDriver

    def __init__(
            self,
            resource_group,
            name,
            driver: AzureResourceManagementStorageDriver,
            driver_storage: Optional[AzureBlobsOAuth2StorageDriver] = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_storage = name
        self.__driver = driver
        self.__driver_storage = driver_storage or driver.get_storage(name, resource_group)
        raise NotImplementedError
