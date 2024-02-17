# SPDX-License-Identifier: GPL-2.0-or-later

import pytest


@pytest.fixture
def mock_env_xdg(monkeypatch, tmp_path):
    ret = {}

    def patch(name, path):
        ret[name] = path
        monkeypatch.setenv(f'XDG_{name.upper()}', path.as_posix())
        path.mkdir(parents=True, exist_ok=True)

    patch('config_dirs', tmp_path / 'xdg' / 'dir' / 'config')
    patch('config_home', tmp_path / 'xdg' / 'home' / 'config')
    return ret
