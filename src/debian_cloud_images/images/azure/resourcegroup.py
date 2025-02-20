# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    ClassVar,
    Self,
)

from .base import ImagesAzureBase


logger = logging.getLogger(__name__)


@dataclass
class ImagesAzureResourcegroup(ImagesAzureBase):
    api_version: ClassVar[str] = '2021-04-01'

    parent: Self = field(init=False, repr=False)

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.conn.subscription_id}/resourceGroups/{self.name}'
