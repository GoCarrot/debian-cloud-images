# SPDX-License-Identifier: GPL-2.0-or-later

from .base import cli_internal, BaseCommand


@cli_internal.register(
    'config-dump',
    help='',
)
class ConfigdumpCommand(BaseCommand):
    def __call__(self):
        self._config.dump()
        self._config_image.dump()


if __name__ == '__main__':
    cli_internal.main(ConfigdumpCommand)
