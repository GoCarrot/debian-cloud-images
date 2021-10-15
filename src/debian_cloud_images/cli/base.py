import argparse
import logging
import os
import typing

from ..utils import argparse_ext
from ..utils.config import Config
from ..utils.config_image import ConfigImageLoader


class BaseCommand:
    _marker = object()

    argparser_name: typing.Optional[str] = None
    argparser_epilog: typing.Optional[str] = None
    argparser_help: typing.Optional[str] = None
    argparser_usage: typing.Optional[str] = None

    @classmethod
    def _argparse_init_sub(cls, subparsers):
        parser = subparsers.add_parser(
            name=cls.argparser_name,
            epilog=cls.argparser_epilog,
            help=cls.argparser_help,
            usage=cls.argparser_usage,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        cls._argparse_register(parser)
        return parser

    @classmethod
    def _argparse_register(cls, parser):
        parser.set_defaults(cls=cls)
        parser.add_argument(
            '--config',
            action=argparse_ext.HashAction,
            help='override config option',
        )
        parser.add_argument(
            '--config-file',
            action='append',
            dest='config_files',
            help='use config file',
            metavar='FILE',
        )
        parser.add_argument(
            '--config-section',
            help='use section from config file',
            metavar='SECTION',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='enable debug output',
        )

    @classmethod
    def _main(cls):
        parser = argparse.ArgumentParser(
            epilog=cls.argparser_epilog,
            prog=cls.argparser_name,
            usage=cls.argparser_usage,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        cls._argparse_register(parser)
        args = parser.parse_args()
        return cls(argparser=parser, **vars(args))()

    def __init__(self, *, argparser=None, cls=None, config={}, config_files=[], config_section=None, debug=False):
        logging.basicConfig(
            level=debug and logging.DEBUG or logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
        )

        config_overrides = [config]
        if argparser is not None:
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

        self.argparser = argparser

    def __call__(self):
        raise NotImplementedError

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
        if default == self._marker:
            self.argparser.error(f'the following config option is required: {keys[0]}')
        return default
