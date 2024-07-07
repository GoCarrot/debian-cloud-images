# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import collections.abc
import importlib.resources
import json
import logging
import pathlib
import re

from datetime import datetime

from .base import cli, BaseCommand

from .. import resources
from ..build.fai import RunFAI
from ..build.manifest import CreateManifest
from ..build.tar import RunTar
from ..utils import argparse_ext


logger = logging.getLogger()


class BuildId:
    re = re.compile(r"^[a-z][a-z0-9-]+$")

    def __init__(self, s):
        r = self.re.match(s)

        if not r:
            raise ValueError('invalid build id value')

        self.id = r.group(0)


class Classes(collections.abc.MutableSet):
    def __init__(self):
        self.__data = []

    def __contains__(self, v):
        return v in self.__data

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def add(self, v):
        logger.info('Adding class %s', v)
        self.__data.append(v)

    def discard(self, v):
        logger.info('Removing class %s', v)
        self.__data.remove(v)

    def update_combine(self, *others):
        new = []
        for other in others:
            for o in other:
                for i in self.__data:
                    new.append('+'.join((i, o)))
                new.append(o)
        self.__data.extend(new)


class Check:
    def __init__(self):
        self.classes = Classes()
        self.classes.add('BUILD_IMAGE')
        self.classes.add('BASE')
        self.classes.add('DEBIAN')
        self.env = {}
        self.info = {}

    def set_type(self, _type):
        self.type = _type
        self.info['type'] = self.type.name
        self.classes.update_combine(self.type.fai_classes)

    def set_release(self, release):
        self.release = release
        self.info['release'] = self.release.basename
        self.info['release_id'] = self.release.id
        self.info['release_baseid'] = self.release.baseid
        self.classes.update_combine(self.release.fai_classes)

    def set_vendor(self, vendor):
        self.vendor = vendor
        self.env['CLOUD_RELEASE_ID'] = self.info['vendor'] = self.vendor.name
        self.classes.update_combine(self.vendor.fai_classes)

    def set_arch(self, arch):
        self.arch = arch
        self.info['arch'] = arch.name
        self.classes.update_combine(arch.fai_classes)

    def set_version(self, version, version_date, build_id):
        self.build_id = self.info['build_id'] = build_id.id

        self.version = self.type.output_version.format(
            version=version,
            date=version_date.strftime('%Y%m%d'),
        )
        self.version_azure = self.type.output_version_azure.format(
            version=version,
            date=version_date.strftime('%Y%m%d'),
        )

        self.env['CLOUD_RELEASE_VERSION'] = self.info['version'] = self.version
        if self.vendor.name == 'azure':
            self.env['CLOUD_RELEASE_VERSION_AZURE'] = self.info['version_azure'] = self.version_azure

    def check(self):
        self.classes.add('LAST')


def _argparse_type_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Given date ({0}) is not valid. Expected format: 'YYYY-MM-DD'".format(s)
        raise argparse.ArgumentTypeError(msg)


@cli.register(
    'build',
    help='build Debian images',
    arguments=[
        cli.prepare_argument(
            'release_name',
            help='Debian release to build',
            metavar='RELEASE',
        ),
        cli.prepare_argument(
            'vendor_name',
            help='Vendor to build image for',
            metavar='VENDOR',
        ),
        cli.prepare_argument(
            'arch_name',
            help='Architecture or sub-architecture to build image for',
            metavar='ARCH',
        ),
        cli.prepare_argument(
            '--build-id',
            metavar='ID',
            required=True,
            type=BuildId,
        ),
        cli.prepare_argument(
            '--build-type',
            default='dev',
            dest='build_type_name',
            help='Type of image to build',
            metavar='TYPE',
        ),
        cli.prepare_argument(
            '--noop',
            action='store_true',
            help='print the commands which would be executed, but do not run them'
        ),
        cli.prepare_argument(
            '--localdebs',
            action='store_true',
            help='Read extra debs from localdebs directory',
        ),
        cli.prepare_argument(
            '--output',
            default='.',
            help='write manifests and images to (default: .)',
            metavar='DIR',
            type=pathlib.Path
        ),
        cli.prepare_argument(
            '--override-name',
            help='override name of output',
        ),
        cli.prepare_argument(
            '--version',
            action=argparse_ext.ActionEnv,
            env='CI_PIPELINE_IID',
            help='version of image',
            metavar='VERSION',
            type=int,
        ),
        cli.prepare_argument(
            '--version-date',
            default=datetime.now(),
            help='date part of version (default: today)',
            type=_argparse_type_date,
        ),
    ],
)
class BuildCommand(BaseCommand):
    def __init__(self, *, release_name=None, vendor_name=None, arch_name=None, version=None, build_id=None, build_type_name=None, localdebs=False, output=None, noop=False, override_name=None, version_date=None, **kw):
        super().__init__(**kw)

        arch = self.config_image.archs.get(arch_name)
        build_type = self.config_image.types.get(build_type_name)
        release = self.config_image.releases.get(release_name)
        vendor = self.config_image.vendors.get(vendor_name)

        if arch is None:
            self.error(
                f'argument ARCH: invalid value: {arch_name}, select one of {", ".join(self.config_image.archs)}'
            )

        if build_type is None:
            self.error(
                f'argument BUILD_TYPE: invalid value: {build_type_name}, select one of {", ".join(self.config_image.types)}'
            )

        if vendor is None:
            self.error(
                f'argument VENDOR: invalid value: {vendor_name}, select one of {", ".join(self.config_image.vendors)}'
            )

        if release is None:
            self.error(
                f'argument RELEASE: invalid value: {release_name}, select one of {", ".join(self.config_image.releases)}'
            )

        self.noop = noop

        self.c = Check()
        self.c.set_type(build_type)
        self.c.set_release(release)
        self.c.set_vendor(vendor)
        self.c.set_arch(arch)
        self.c.set_version(version, version_date, build_id)
        if localdebs:
            self.c.classes.add('LOCALDEBS')
        self.c.check()

        name = override_name or self.c.type.output_name.format(
            build_type=self.c.type.name,
            release=self.c.release.name,
            vendor=self.c.vendor.name,
            arch=self.c.arch.name,
            version=self.c.version,
            build_id=self.c.build_id,
        )

        with importlib.resources.as_file(importlib.resources.files(resources) / 'system_tests') as p_system_tests:
            self.env = self.c.env
            self.env['CLOUD_BUILD_INFO'] = json.dumps(self.c.info)
            self.env['CLOUD_BUILD_NAME'] = name
            self.env['CLOUD_BUILD_OUTPUT_DIR'] = output.resolve()
            self.env['CLOUD_BUILD_SYSTEM_TESTS'] = p_system_tests.as_posix()

            output.mkdir(parents=True, exist_ok=True)

            image_raw = output / '{}.raw'.format(name)
            image_tar = output / '{}.tar'.format(name)
            manifest_dpkg_status = output / '{}.dpkg-status'.format(name)
            manifest_final = output / '{}.build.json'.format(name)

            self.fai = RunFAI(
                output_filename=image_raw,
                release=self.c.release.basename,
                classes=self.c.classes,
                size_gb=self.c.vendor.size,
                env=self.env,
            )

            self.tar = RunTar(
                input_filename=image_raw,
                output_filename=image_tar,
            )

            self.manifest = CreateManifest(
                dpkg_status=manifest_dpkg_status,
                output_filename=manifest_final,
                info=self.c.info,
            )

    def __call__(self):
        self.fai(not self.noop)
        digest = self.tar(not self.noop)
        self.manifest.write(not self.noop, (digest,))


if __name__ == '__main__':
    cli.main(BuildCommand)
