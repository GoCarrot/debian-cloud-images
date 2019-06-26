import argparse
import configparser
import logging
import os
import pathlib


class BaseCommand:
    argparser_name = None
    argparser_help = None
    argparser_usage = None

    @classmethod
    def _argparse_init_sub(cls, subparsers):
        parser = subparsers.add_parser(
            formatter_class=argparse.RawTextHelpFormatter,
            name=cls.argparser_name,
            help=cls.argparser_help,
            usage=cls.argparser_usage,
        )
        cls._argparse_register(parser)
        return parser

    @classmethod
    def _argparse_register(cls, parser):
        parser.set_defaults(cls=cls)
        parser.add_argument(
            '--debug',
            action='store_true',
            help='enable debug output',
        )

    @staticmethod
    def _config_files():
        path = os.getenv('XDG_CONFIG_DIRS', '/etc/xdg')
        for p in path.split(os.pathsep):
            yield pathlib.Path(p).expanduser() / 'debian-cloud-images' / 'config'
        path = os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config"))
        for p in path.split(os.pathsep):
            yield pathlib.Path(p).expanduser() / 'debian-cloud-images' / 'config'

    @classmethod
    def _config_read(cls):
        config = configparser.ConfigParser()
        config.read(cls._config_files())
        return config

    @classmethod
    def _main(cls):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            usage=cls.argparser_usage,
        )
        cls._argparse_register(parser)
        args = parser.parse_args()
        return cls(**vars(args))()

    def __init__(self, *, cls=None, debug=False):
        logging.basicConfig(
            level=debug and logging.DEBUG or logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
        )

    def __call__(self):
        raise NotImplementedError
