# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.cli.base import BaseCommand


@pytest.fixture
def config_path(tmp_path):
    with tmp_path.joinpath('config.yml').open('w') as f:
        print("""
---
azure:
  cloudpartner:
    tenant: 7122190e-711a-11ef-9288-37554fc77a04
    publisher: debian
""", file=f)
    return tmp_path


def test():
    BaseCommand()


def test_config_get(config_path):
    b = BaseCommand(config_files=[config_path / 'config.yml'])
    v = b.config_get('azure.cloudpartner.tenant')
    assert str(v) == '7122190e-711a-11ef-9288-37554fc77a04'


def test_config_get_with_env_override(config_path, monkeypatch):
    monkeypatch.setenv('DCI_CONFIG_azure_cloudpartner_publisher', 'yggdrasil')
    b = BaseCommand(config_files=[config_path / 'config.yml'])
    v = b.config_get('azure.cloudpartner.publisher')
    assert v == 'yggdrasil'
