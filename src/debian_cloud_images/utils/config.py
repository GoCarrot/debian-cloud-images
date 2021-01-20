import configparser
import marshmallow
import os
import pathlib
import sys
import yaml

from ..api.meta import ObjectMeta
from ..api.cdo.tool_config import v1alpha1_ToolConfigSchema
from ..api.registry import registry as api_registry


def items_nested(d, suffixes=[]):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from items_nested(v, suffixes + [k])
    else:
        yield (suffixes, d)


def flatten_dict(d):
    return {'.'.join(ks): v for ks, v in items_nested(d)}


class Config:
    def __init__(self, overrides=[]):
        self._configs_default = []
        self._configs_override = []
        self._configs = {}

        for override in overrides:
            config = api_registry.load(override, default_typemeta=v1alpha1_ToolConfigSchema.__typemeta__, unknown=marshmallow.INCLUDE)
            self._configs_override.append(flatten_dict(config))

    @classmethod
    def _default_filenames(cls, *names):
        paths = []
        paths.extend(os.getenv('XDG_CONFIG_HOME', '~/.config').split(os.pathsep))
        paths.extend(os.getenv('XDG_CONFIG_DIRS', '/etc/xdg').split(os.pathsep))
        for path in paths:
            for name in names:
                yield pathlib.Path(path).expanduser() / 'debian-cloud-images' / name

    @classmethod
    def _default_files(cls, *names):
        for p in cls._default_filenames(*names):
            if p.exists():
                with p.open() as f:
                    yield f

    def read(self, *filenames):
        for filename in filenames:
            with open(filename) as f:
                try:
                    self.read_yaml((f, ))
                except yaml.parser.ParserError:
                    self.read_configparser((f, ))

    def read_defaults(self):
        self.read_yaml(self._default_files('config.yml', 'config.yaml'))
        self.read_configparser(self._default_files('config'))

    def read_configparser(self, files):
        config = configparser.ConfigParser()
        for f in files:
            config.read_file(f)
        self._configs_default.append(config.defaults())
        # XXX: Uses internal _sections variable
        for name, section in config._sections.items():
            self._configs.setdefault(f'_name={name}', []).append(dict(section))

    def read_yaml(self, files, unknown=marshmallow.RAISE):
        for f in files:
            for config_raw in yaml.safe_load_all(f):
                config = api_registry.load(config_raw, default_typemeta=v1alpha1_ToolConfigSchema.__typemeta__, unknown=unknown)
                config_metadata = config.pop('metadata', ObjectMeta())
                config_name = config_metadata.name
                config_flat = flatten_dict(config)
                if config_name:
                    self._configs.setdefault(f'_name={config_name}', []).append(config_flat)
                else:
                    self._configs_default.append(config_flat)

    def dump(self, f=sys.stdout):
        self._dump_list(f, 'Default', self._configs_default)
        self._dump_list(f, 'Override', self._configs_override)
        for k, v in sorted(self._configs.items()):
            self._dump_list(f, f'Selector {k}', v)

    @classmethod
    def _dump_list(cls, f, header, data):
        for i, item in enumerate(i for i in data if i):
            print(f'{header} ({i}):', file=f)
            for key, value in sorted(item.items()):
                print(f'    {key}: {value}', file=f)
            print(file=f)

    def __getitem__(self, key):
        configs = []
        # Reverse lists, so first value will have precedence
        configs.extend(self._configs_default[::-1])
        if key is not None:
            configs.extend(self._configs[key][::-1])
        configs.extend(self._configs_override[::-1])
        ret = {}
        for c in configs:
            ret.update(c)
        return ret
