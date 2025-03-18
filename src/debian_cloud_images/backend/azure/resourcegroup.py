# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import ClassVar

from .base import AzureBase
from .subscription import AzureSubscription


logger = logging.getLogger(__name__)


@dataclass
class AzureResourcegroup(AzureBase[AzureSubscription]):
    api_version: ClassVar[str] = '2021-04-01'

    @property
    def path(self) -> str:
        return f'{self.parent.path}/resourceGroups/{self.name}'
