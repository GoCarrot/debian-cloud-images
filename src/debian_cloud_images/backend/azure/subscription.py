# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import httpx
import logging

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    ClassVar,
    Self,
)

from .base import AzureBase


logger = logging.getLogger(__name__)


@dataclass
class AzureSubscription(AzureBase):
    api_version: ClassVar[str] = '2024-11-01'

    parent: Self = field(init=False, repr=False)
    _client: httpx.Client

    @property
    def client(self) -> httpx.Client:
        return self._client

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.name}'
