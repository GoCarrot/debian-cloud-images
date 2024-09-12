# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import argparse
import logging
import os

from .registry import CliRegistry
from .registry import CliCommand
from ..utils import argparse_ext
from ..utils.config import Config
from ..utils.config_image import ConfigImageLoader


cli = CliRegistry(
    argparse.ArgumentParser(
        allow_abbrev=False,
        prog='debian-cloud-images',
        formatter_class=argparse.RawTextHelpFormatter,
    ),
    arguments=[
        CliRegistry.prepare_argument(
            '--config',
            action=argparse_ext.HashAction,
            help='override config option',
        ),
        CliRegistry.prepare_argument(
            '--config-file',
            action='append',
            dest='config_files',
            help='use config file',
            metavar='FILE',
        ),
        CliRegistry.prepare_argument(
            '--config-section',
            help='use section from config file',
            metavar='SECTION',
        ),
        CliRegistry.prepare_argument(
            '--debug',
            action='store_true',
            help='enable debug output',
        ),
    ]
)


cli_internal = cli.register_subparsers(
    'internal',
    help='',
)


class BaseCommand(CliCommand):
    _marker = object()

    def __init__(self, *, config={}, config_files=[], config_section=None, debug=False, **kw):
        super().__init__(**kw)

        logging.basicConfig(
            level=debug and logging.DEBUG or logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
        )

        config_overrides = [config]
        config_overrides.insert(0, self.config_env())
        self._config = Config(overrides=config_overrides)
        if config_files:
            self._config.read(*config_files)
        else:
            self._config.read_defaults()

        if config_section:
            self.config = self._config[f'_name={config_section}']
        else:
            self.config = self._config[None]

        self._config_image = ConfigImageLoader()
        self._config_image.read_defaults()
        self.config_image = self._config_image.config

    def __config_env_compat(self, subitem, kin, key):
        v = os.environ.get(kin)
        if v is not None:
            kl = key.split('.')
            for k in kl[:-1]:
                subitem = subitem.setdefault(k, {})
            subitem[kl[-1]] = v

    def config_env(self):
        ret = {}

        self.__config_env_compat(
            ret, 'AWS_ACCESS_KEY_ID', 'ec2.auth.key')
        self.__config_env_compat(
            ret, 'AWS_SECRET_ACCESS_KEY', 'ec2.auth.secret')
        self.__config_env_compat(
            ret, 'AWS_SESSION_TOKEN', 'ec2.auth.token')
        self.__config_env_compat(
            ret, 'GOOGLE_APPLICATION_CREDENTIALS', 'gce.auth.credentialsfile')

        for k, v in os.environ.items():
            if k.startswith('DCI_CONFIG_'):
                subitem = ret
                kl = [i.lower() for i in k.split('_')[2:]]
                for k in kl[:-1]:
                    subitem = subitem.setdefault(k, {})
                subitem[kl[-1]] = v

        return ret

    def config_get(self, *keys, default=_marker):
        for key in keys:
            ret = self.config.get(key, self._marker)
            if ret != self._marker:
                return ret
        if default == self._marker and self.argparser is not None:
            self.argparser.error(f'the following config option is required: {keys[0]}')
        return default
