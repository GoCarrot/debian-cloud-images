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
    def _argparse_init_sub(cls, subparsers, config, config_section):
        parser = subparsers.add_parser(
            formatter_class=argparse.RawTextHelpFormatter,
            name=cls.argparser_name,
            help=cls.argparser_help,
            usage=cls.argparser_usage,
        )
        if config_section:
            section = config[config_section]
        else:
            try:
                section = config[cls.argparser_name]
            except KeyError:
                section = config.defaults()
        cls._argparse_register_config(parser)
        cls._argparse_register(parser, section)
        return parser

    @classmethod
    def _argparse_register(cls, parser, config):
        parser.set_defaults(cls=cls)
        parser.add_argument(
            '--debug',
            action='store_true',
            help='enable debug output',
        )

    @classmethod
    def _argparse_register_config(cls, parser):
        parser.add_argument(
            '--config-file',
            help='Use config file',
            metavar='FILE',
        )
        parser.add_argument(
            '--config-section',
            help='Use section from config file',
            metavar='SECTION',
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
    def _config_read(cls, config_file):
        config = configparser.ConfigParser()
        if config_file:
            with open(config_file) as f:
                config.read_file(f)
        else:
            config.read(cls._config_files())
        return config

    @classmethod
    def _main(cls):
        early_parser = argparse.ArgumentParser(
            add_help=False,
            allow_abbrev=False,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        cls._argparse_register_config(early_parser)
        early_args, remainder_argv = early_parser.parse_known_args()

        config = cls._config_read(early_args.config_file)
        parser = argparse.ArgumentParser(
            allow_abbrev=False,
            formatter_class=argparse.RawTextHelpFormatter,
            usage=cls.argparser_usage,
        )
        if early_args.config_section:
            section = config[early_args.config_section]
        else:
            try:
                section = config[cls.argparser_name]
            except KeyError:
                section = config.defaults()
        cls._argparse_register_config(parser)
        cls._argparse_register(parser, section)
        args = parser.parse_args(remainder_argv)
        return cls(**vars(args))()

    def __init__(self, *, cls=None, config_file=None, config_section=None, debug=False):
        logging.basicConfig(
            level=debug and logging.DEBUG or logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
        )

    def __call__(self):
        raise NotImplementedError
