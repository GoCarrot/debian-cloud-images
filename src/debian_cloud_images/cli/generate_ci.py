import argparse
import json
import logging
import sys
import typing

from .base import BaseCommand


logger = logging.getLogger()


class GenerateCiCommand(BaseCommand):
    argparser_name = 'generate-generate'
    argparser_help = 'generate CI config'
    argparser_usage = '%(prog)s'
    argparser_argument_public_type = None

    @classmethod
    def _argparse_register(cls, parser) -> None:
        super()._argparse_register(parser)

        cls.argparser_argument_public_type = parser.add_argument(
            '--public-type',
            default='dev',
            dest='public_type_name',
            help='the public type to generate config for',
            metavar='TYPE',
        )
        parser.add_argument(
            'output',
            metavar='OUTPUT',
            nargs='?',
            help='Where to write file to (default: stdout)',
        )

    def __init__(self, *, output: str, public_type_name: str, **kw):
        super().__init__(**kw)

        self.public_type = self.config_image.public_types.get(public_type_name)

        if self.public_type is None:
            raise argparse.ArgumentError(
                self.argparser_argument_public_type,
                f'invalid value: {public_type_name}, select one of {", ".join(self.config_image.public_types)}')

        self.output = output

    def check_matches(self, matches, release_name, arch_name):
        if not matches:
            return True

        for m in matches:
            if not m.match_releases:
                pass
            elif release_name in m.match_releases:
                pass
            elif '*' in m.match_releases:
                pass
            else:
                continue

            if not m.match_arches:
                pass
            elif arch_name in m.match_arches:
                pass
            elif '*' in m.match_arches:
                pass
            else:
                continue

            if m.op == 'Enable':
                return True
            elif m.op == 'Disable':
                return False

        return False

    def __call__(self) -> None:
        out = {}

        for vendor_name, vendor in self.config_image.vendors.items():
            for release_name, release in self.config_image.releases.items():
                for arch_name, arch in self.config_image.archs.items():
                    if not self.check_matches(vendor.matches, release.basename, arch_name):
                        continue

                    name = ' '.join((vendor_name, release_name, arch_name, 'build'))

                    out[name] = {
                        'extends': '.build',
                        'variables': {
                            'CLOUD_ARCH': arch_name,
                            'CLOUD_RELEASE': release_name,
                            'CLOUD_VENDOR': vendor_name,
                        }
                    }

        if self.output:
            with open(self.output, 'w') as f:
                self.dump(f, out)
        else:
            self.dump(sys.stdout, out)

    def dump(self, f: typing.TextIO, data: typing.Any) -> None:
        print(f'# Generated with "python3 -m debian_cloud_images.cli.generate_ci {" ".join(sys.argv[1:])}"', file=f)
        json.dump(data, f, indent=2)
        print(file=f)


if __name__ == '__main__':
    GenerateCiCommand._main()
