# SPDX-License-Identifier: GPL-2.0-or-later

import os
import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k, v in os.environ.items():
        if k.startswith('DCI_CONFIG_') or k.startswith('AWS_') or k.startswith('GNOME_'):
            monkeypatch.delenv(k)
