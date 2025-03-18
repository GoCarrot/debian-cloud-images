# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import ClassVar

from .base import AzureBase
from .resourcegroup import AzureResourcegroup


logger = logging.getLogger(__name__)


@dataclass
class AzureComputegallery(AzureBase[AzureResourcegroup]):
    api_version: ClassVar[str] = '2024-03-03'

    @property
    def path(self) -> str:
        return f'{self.parent.path}/providers/Microsoft.Compute/galleries/{self.name}'
