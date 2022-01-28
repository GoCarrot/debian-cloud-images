from .base import BaseCommand


class ConfigdumpCommand(BaseCommand):
    def __call__(self):
        self._config.dump()
        self._config_image.dump()


if __name__ == '__main__':
    ConfigdumpCommand._main()
