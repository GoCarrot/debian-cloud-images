import json
import logging
import sys

from .base import BaseCommand


logger = logging.getLogger()


class GenerateCiCommand(BaseCommand):
    argparser_name = 'generate-generate'
    argparser_help = 'generate CI config'
    argparser_usage = '%(prog)s'

    def __call__(self) -> None:
        out = {}

        for vendor_name, vendor in self.config_image.vendors.items():
            builds = []

            for release_name, release in self.config_image.releases.items():
                # XXX: Better selection
                if vendor_name == 'gce' and release_name == 'bullseye':
                    continue

                for arch_name, arch in self.config_image.archs.items():
                    # XXX: Better arch selection
                    if vendor_name in ('azure', 'ec2', 'gce'):
                        if arch_name == 'amd64':
                            pass
                        elif arch_name == 'arm64':
                            if vendor_name not in ('ec2', ):
                                continue
                        else:
                            continue

                    name = ' '.join((vendor_name, release_name, arch_name, 'build'))
                    extends = '.' + ' '.join((vendor_name, 'build'))

                    builds.append(name)
                    out[name] = {
                        'extends': extends,
                        'variables': {
                            'CLOUD_ARCH': arch_name,
                            'CLOUD_RELEASE': release_name,
                            'CLOUD_VENDOR': vendor_name,
                        }
                    }

            # XXX: Better selection
            if vendor_name in ('azure', 'ec2', 'gce'):
                name = ' '.join((vendor_name, 'upload'))
                extends = '.' + name
                out[name] = {
                    'extends': extends,
                    'dependencies': builds,
                }

        print('# Generated with "python3 -m debian_cloud_images.cli.generate_ci"', file=sys.stdout)
        json.dump(out, sys.stdout, indent=2)


if __name__ == '__main__':
    GenerateCiCommand._main()
