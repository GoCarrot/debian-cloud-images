# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import enum


class AzureVmArch(enum.Enum):
    amd64 = 'x64'
    arm64 = 'arm64'


class AzureVmGeneration(enum.Enum):
    v1 = 'V1'
    v2 = 'V2'
