# SPDX-License-Identifier: GPL-2.0-or-later

import io
import marshmallow

from debian_cloud_images.utils.config import Config


class TestConfig:
    def test_default_filenames(self, monkeypatch):
        monkeypatch.setenv('XDG_CONFIG_DIRS', '/dirs1/root:/dirs2/root')
        monkeypatch.setenv('XDG_CONFIG_HOME', '/home1/root:/home2/root')

        filenames = [i.as_posix() for i in Config._default_filenames('name')]

        assert filenames == [
            '/home1/root/debian-cloud-images/name',
            '/home2/root/debian-cloud-images/name',
            '/dirs1/root/debian-cloud-images/name',
            '/dirs2/root/debian-cloud-images/name',
        ]

    def test_default_files(self, mock_env_xdg):
        assert len(list(Config._default_files('name'))) == 0

    def test_default_files_exist(self, mock_env_xdg):
        for i in ('config_dirs', 'config_home'):
            configfile_dir = mock_env_xdg[i] / 'debian-cloud-images'
            configfile_dir.mkdir()
            configfile = configfile_dir / 'name'
            configfile.write_text(i)

        files = [f.read() for f in Config._default_files('name')]

        assert files == [
            'config_home',
            'config_dirs',
        ]

    def test_read_configparser(self):
        c = Config()
        c.read_configparser([io.StringIO("""
[DEFAULT]
default: default
test: default

[section1]
test: section1
""")])

        assert c._configs_default == [
            {
                'default': 'default',
                'test': 'default',
            }
        ]
        assert c._configs == {
            '_name=section1': [
                {
                    'test': 'section1',
                }
            ]
        }

    def test_read_yaml(self):
        c = Config()
        c.read_yaml([io.StringIO("""
---
default: default
test: default
nested:
  key1: test
list:
- test1
- test2
---
metadata:
  name: section1
test: section1
""")], unknown=marshmallow.INCLUDE)

        assert c._configs_default == [
            {
                'default': 'default',
                'test': 'default',
                'nested.key1': 'test',
                'list': ['test1', 'test2'],
            }
        ]
        assert c._configs == {
            '_name=section1': [
                {
                    'test': 'section1',
                }
            ]
        }

    def test__getitem__(self):
        c = Config()
        c._configs_default = [
            {
                'default': 'default',
                'override': 'default',
            }
        ]
        c._configs = {
            '_name=section1': [
                {
                    'section': 'section1',
                }
            ]
        }
        c._configs_override = [
            {
                'override': 'override',
            }
        ]

        assert c[None] == {
            'default': 'default',
            'override': 'override',
        }
        assert c['_name=section1'] == {
            'default': 'default',
            'section': 'section1',
            'override': 'override',
        }

    def test__getitem___precedence(self):
        c = Config()
        c._configs_default = [
            {
                'default': 'value1',
            },
            {
                'default': 'value2',
            }
        ]
        c._configs = {
            '_name=section1': [
                {
                    'section': 'value1',
                },
                {
                    'section': 'value2',
                }
            ]
        }
        c._configs_override = [
            {
                'override': 'value1',
            },
            {
                'override': 'value2',
            }
        ]

        assert c['_name=section1'] == {
            'default': 'value1',
            'section': 'value1',
            'override': 'value1',
        }
