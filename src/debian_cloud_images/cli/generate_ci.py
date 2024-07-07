# SPDX-License-Identifier: GPL-2.0-or-later

import json
import logging
import sys
import typing

from .base import cli_internal, BaseCommand


logger = logging.getLogger()


class SortedList:
    def __init__(self, d=(), *, key):
        self.__data = list(d)
        self.__key = key

    def __len__(self):
        return len(self.__data)

    def add(self, d):
        if d not in self.__data:
            self.__data.append(d)
        return self.__data

    def copy(self):
        return self.__class__(self.__data, key=self.__key)

    def sorted(self):
        return sorted(self.__data, key=lambda s: s.get(self.__key, '\uFFFF'))


class JSONSortedEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SortedList):
            # GitLab only allows 50 entries in 'needs' by default
            assert len(obj) < 50
            return obj.sorted()
        return super().default(self, obj)


@cli_internal.register(
    'generate-ci',
    help='generate CI config',
    usage='%(prog)s',
    arguments=[
        cli_internal.prepare_argument(
            '--public-type',
            default='dev',
            dest='public_type_name',
            help='the public type to generate config for',
            metavar='TYPE',
        ),
        cli_internal.prepare_argument(
            'output',
            metavar='OUTPUT',
            nargs='?',
            help='Where to write file to (default: stdout)',
        ),
    ],
)
class GenerateCiCommand(BaseCommand):
    def __init__(self, *, output: str, public_type_name: str, **kw):
        super().__init__(**kw)

        self.public_type = self.config_image.public_types.get(public_type_name)

        if self.public_type is None:
            self.error(
                f'argument --public-type: invalid value: {public_type_name}, select one of {", ".join(self.config_image.public_types)}'
            )

        self.output = output

    def check_matches(self, matches, vendor_name, release_name, arch_name):
        if not matches:
            return True, False, None

        enable = None
        enable_upload = None
        upload_group = None

        for m in matches:
            if not m.match_vendors:
                pass
            elif vendor_name in m.match_vendors:
                pass
            elif '*' in m.match_vendors:
                pass
            else:
                continue

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
                if enable is None:
                    enable = True
            elif m.op == 'EnableUpload':
                if enable is None:
                    enable = True
                if enable_upload is None:
                    enable_upload = True
            elif m.op == 'Disable':
                if enable is None:
                    enable = False
            elif m.op == 'DisableUpload':
                if enable is None:
                    enable = False
                if enable_upload is None:
                    enable_upload = False

            if upload_group is None:
                upload_group = m.upload_group

        return enable, enable_upload, upload_group

    def __call__(self) -> None:
        out: dict[str, typing.Any] = {}

        for vendor_name, vendor in self.config_image.vendors.items():
            for release_name, release in self.config_image.releases.items():
                for arch_name, arch in self.config_image.archs.items():
                    enable, _, _ = self.check_matches(release.matches, vendor_name, release.basename, arch_name)
                    if not enable:
                        continue

                    enable, _, _ = self.check_matches(vendor.matches, vendor_name, release.basename, arch_name)
                    if not enable:
                        continue

                    enable, enable_upload, upload_group = self.check_matches(self.public_type.matches, vendor_name, release.basename, arch_name)
                    if not enable:
                        continue

                    variables = {
                        'CLOUD_ARCH': arch_name,
                        'CLOUD_RELEASE': release_name,
                        'CLOUD_VENDOR': vendor_name,
                    }
                    variables_upload_all = {
                        'CLOUD_RELEASE': release_name,
                    }
                    variables_postupload = {}

                    name_build = f'{vendor_name} {release_name} {arch_name} build'
                    name_upload = f'{vendor_name} {release_name} {arch_name} upload'
                    name_upload_all = f'{release_name} upload'
                    extends_upload = f'.{vendor_name} upload'
                    extends_postupload = f'.{vendor_name} postupload'
                    needs_build = {
                        'job': name_build,
                        'optional': False,
                    }
                    needs_upload = {
                        'job': name_upload,
                        'optional': False,
                    }
                    needs_upload_optional = {
                        'job': name_upload,
                        'optional': True,
                    }
                    enable_variable = f'PIPELINE_RELEASE_{release_name.upper().replace("-", "_")}'

                    # XXX
                    if self.public_type.name == 'release':
                        enable_build = False
                        enable_upload_all = True
                        rule = {'if': f'${enable_variable}'}
                    elif self.public_type.name == 'daily':
                        enable_build = True
                        enable_upload_all = True
                        rule = {'if': f'${enable_variable}'}
                        out.setdefault('variables', {})[enable_variable] = '1'
                    else:
                        enable_build = True
                        enable_upload_all = False
                        rule = {'when': 'manual'}

                    if enable_upload_all:
                        if upload_group:
                            variables['CLOUD_UPLOAD_GROUP'] = upload_group
                            variables_postupload['CLOUD_UPLOAD_GROUP'] = upload_group
                            name_upload_group = f'{vendor_name} group-{upload_group} upload'
                            name_postupload = f'{vendor_name} group-{upload_group} postupload'
                        else:
                            name_upload_group = f'{vendor_name} upload'
                            name_postupload = f'{vendor_name} postupload'

                        job_upload_all: dict[str, typing.Any] = out.setdefault(name_upload_all, {
                            'extends': '.upload',
                            'variables': variables_upload_all,
                            'needs': SortedList(key='job'),
                            'rules': SortedList([], key='if'),
                        })
                        job_upload_all['rules'].add(rule)

                    if enable_build:
                        if enable_upload_all:
                            job_upload_all['needs'].add(needs_build)

                        out[name_build] = {
                            'extends': '.build',
                            'variables': variables,
                            'rules': SortedList([rule], key='if'),
                        }

                    if enable_upload:
                        job_upload_all['needs'].add(needs_upload)
                        job_upload = out[name_upload] = {
                            'extends': extends_upload,
                            'variables': variables,
                            'needs': SortedList(key='job'),
                            'rules': SortedList([rule], key='if'),
                        }

                        if enable_build:
                            job_upload['needs'].add(needs_build)
                        if upload_group:
                            job_upload['resource_group'] = name_upload_group

                        job_postupload: dict[str, typing.Any] = out.setdefault(name_postupload, {
                            'extends': extends_postupload,
                            'variables': variables_postupload,
                            'needs': SortedList(key='job'),
                            'rules': SortedList([], key='if'),
                        })
                        job_postupload['needs'].add(needs_upload_optional)
                        job_postupload['rules'].add(rule)
                        if enable_build:
                            job_postupload['needs'].add(needs_build)

        if self.output:
            with open(self.output, 'w') as f:
                self.dump(f, out)
        else:
            self.dump(sys.stdout, out)

    def dump(self, f: typing.TextIO, data: typing.Any) -> None:
        print(f'# Generated with "debian-cloud-images internal generate-ci --public-type {self.public_type.name}"', file=f)
        json.dump(data, f, indent=2, sort_keys=True, cls=JSONSortedEncoder)
        print(file=f)


if __name__ == '__main__':
    cli_internal.main(GenerateCiCommand)
