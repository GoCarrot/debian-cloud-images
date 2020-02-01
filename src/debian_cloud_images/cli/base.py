import argparse
import logging

from ..utils import argparse_ext
from ..utils.config import Config


class BaseCommand:
    _marker = object()

    argparser_name = None
    argparser_epilog = None
    argparser_help = None
    argparser_usage = None

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

        self._config = Config(override=config)
        if config_files:
            self._config.read(*config_files)
        else:
            self._config.read_defaults()

        if config_section:
            self.config = self._config[f'_name={config_section}']
        else:
            self.config = self._config[None]

        self.argparser = argparser

    def __call__(self):
        raise NotImplementedError

    def config_get(self, *keys, default=_marker):
        for key in keys:
            ret = self.config.get(key, self._marker)
            if ret != self._marker:
                return ret
        if default == self._marker:
            self.argparser.error(f'the following config option is required: {keys[0]}')
        return default
