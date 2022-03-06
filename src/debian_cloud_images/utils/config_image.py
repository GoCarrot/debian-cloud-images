import marshmallow
import os
import pathlib
import sys
import yaml

from ..api.cdo.image_config import v1alpha1_ImageConfigSchema
from ..api.registry import registry as api_registry
from ..resources import open_text as resources_open_text


class ConfigImageLoader(dict):
    @classmethod
    def _default_filenames(cls, *names):
        paths = []
        paths.extend(os.getenv('XDG_CONFIG_HOME', '~/.config').split(os.pathsep))
        paths.extend(os.getenv('XDG_CONFIG_DIRS', '/etc/xdg').split(os.pathsep))
        for path in paths:
            for name in names:
                yield pathlib.Path(path).expanduser() / 'debian-cloud-images' / name

    def read(self, *filenames):
        for filename in filenames:
            with open(filename) as f:
                self.read_yaml((f, ))

    def read_defaults(self):
        for p in self._default_filenames('image.yml', 'image.yaml'):
            if p.exists():
                with p.open() as f:
                    self.read_yaml(f)
                    return

        with resources_open_text('image.yaml') as f:
            self.read_yaml(f)

    def read_yaml(self, f, unknown=marshmallow.RAISE):
        config_raw = yaml.safe_load(f)
        self.config = api_registry.load(config_raw, default_typemeta=v1alpha1_ImageConfigSchema.__typemeta__, unknown=unknown)

    def dump(self, f=sys.stdout):
        yaml.dump(v1alpha1_ImageConfigSchema(context={'registry': api_registry}).dump(self.config), f, explicit_start=True)
        print(file=f)
