# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import httpx
import logging

from dataclasses import dataclass
from typing import ClassVar

from .base import AzureBase
from .client import AzureClient


logger = logging.getLogger(__name__)


@dataclass
class AzureSubscription(AzureBase[AzureClient]):
    api_version: ClassVar[str] = '2024-11-01'

    @property
    def client(self) -> httpx.Client:
        return self.parent

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.name}'
