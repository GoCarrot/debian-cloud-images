import argparse
import collections.abc
import enum
import json
import logging
import pathlib
import re

from datetime import datetime

from .base import BaseCommand

from ..build.fai import RunFAI
from ..build.manifest import CreateManifest
from ..build.tar import RunTar
from ..data import data_path
from ..utils import argparse_ext


logger = logging.getLogger()


class Arch:
    def __init__(self, kw):
        def init(*, fai_classes):
            self.fai_classes = fai_classes
        init(**kw)


class Release:
    def __init__(self, kw):
        def init(*, id, baseid, fai_classes, arch_supports_linux_image_cloud):
            self.id = id
            self.baseid = baseid
            self.fai_classes = fai_classes
            self.arch_supports_linux_image_cloud = arch_supports_linux_image_cloud
        init(**kw)

    def supports_linux_image_cloud_for_arch(self, arch):
        if arch in self.arch_supports_linux_image_cloud:
            return True
        return False


class Vendor:
    def __init__(self, kw):
        def init(*, fai_size, fai_classes, use_linux_image_cloud=False):
            self.fai_size = fai_size
            self.fai_classes = fai_classes
            self.use_linux_image_cloud = use_linux_image_cloud
        init(**kw)


class BuildType:
    def __init__(self, kw):
        def init(*, fai_classes, output_name, output_version, output_version_azure):
            self.fai_classes = fai_classes
            self.output_name = output_name
            self.output_version = output_version
            self.output_version_azure = output_version_azure
        init(**kw)


ArchEnum = enum.Enum(  # type:ignore
                       # mypy is not able to parse functional Enum properly
    'ArchEnum',
    {
        'amd64': {
            'fai_classes': ('AMD64', 'GRUB_CLOUD_AMD64'),
        },
        'arm64': {
            'fai_classes': ('ARM64', 'GRUB_EFI_ARM64'),
        },
        'ppc64el': {
            'fai_classes': ('PPC64EL', 'GRUB_IEEE1275'),
        },
    },
    type=Arch,
)


ReleaseEnum = enum.Enum(  # type:ignore
                          # mypy is not able to parse functional Enum properly
    'ReleaseEnum',
    {
        'buster': {
            'id': '10',
            'baseid': '10',
            'fai_classes': ('BUSTER', 'EXTRAS'),
            'arch_supports_linux_image_cloud': ('amd64',),
        },
        'buster-backports': {
            'id': '10-backports',
            'baseid': '10',
            'fai_classes': ('BUSTER', 'BACKPORTS_LINUX', 'EXTRAS'),
            'arch_supports_linux_image_cloud': ('amd64',),
        },
        'bullseye': {
            'id': '11',
            'baseid': '11',
            'fai_classes': ('BULLSEYE', ),
            'arch_supports_linux_image_cloud': ('amd64', 'arm64',),
        },
        'sid': {
            'id': 'sid',
            'baseid': 'sid',
            'fai_classes': ('SID', 'EXTRAS'),
            'arch_supports_linux_image_cloud': ('amd64', 'arm64',),
        },
    },
    type=Release,
)


VendorEnum = enum.Enum(  # type:ignore
                         # mypy is not able to parse functional Enum properly
    'VendorEnum',
    {
        'azure': {
            'fai_size': '30G',
            'fai_classes': ('AZURE', 'IPV6_DHCP'),
            'use_linux_image_cloud': True,
        },
        'ec2': {
            'fai_size': '8G',
            'fai_classes': ('EC2', 'IPV6_DHCP'),
            'use_linux_image_cloud': True,
        },
        'gce': {
            'fai_size': '10G',
            'fai_classes': ('GCE', ),
            'use_linux_image_cloud': True,
        },
        'generic': {
            'fai_size': '2G',
            'fai_classes': ('GENERIC', ),
        },
        'genericcloud': {
            'fai_size': '2G',
            'fai_classes': ('GENERIC', ),
            'use_linux_image_cloud': True,
        },
        'nocloud': {
            'fai_size': '2G',
            'fai_classes': ('NOCLOUD', ),
        },
    },
    type=Vendor,
)


BuildTypeEnum = enum.Enum(  # type:ignore
                            # mypy is not able to parse functional Enum properly
    'BuildTypeEnum',
    {
        'dev': {
            'fai_classes': ('TYPE_DEV', ),
            'output_name': 'debian-{release}-{vendor}-{arch}-{build_type}-{build_id}-{version}',
            'output_version': '{version}',
            'output_version_azure': '0.0.{version!s}',
        },
        'official': {
            'fai_classes': (),
            'output_name': 'debian-{release}-{vendor}-{arch}-{build_type}-{version}',
            'output_version': '{date}-{version}',
            'output_version_azure': '0.{date!s}.{version!s}',
        },
    },
    type=BuildType,
)


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


class Check:
    def __init__(self):
        self.classes = Classes()
        self.classes.add('DEBIAN')
        self.classes.add('CLOUD')
        self.env = {}
        self.info = {}

    def set_type(self, _type):
        self.type = _type
        self.info['type'] = self.type.name
        self.classes |= self.type.fai_classes

    def set_release(self, release):
        self.release = release
        self.info['release'] = self.release.name
        self.info['release_id'] = self.release.id
        self.info['release_baseid'] = self.release.baseid
        self.classes |= self.release.fai_classes

    def set_vendor(self, vendor):
        self.vendor = vendor
        self.env['CLOUD_RELEASE_ID'] = self.info['vendor'] = self.vendor.name
        self.classes |= self.vendor.fai_classes

    def set_arch(self, arch):
        self.arch = arch
        self.info['arch'] = self.arch.name
        self.classes |= self.arch.fai_classes

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
        if self.release.supports_linux_image_cloud_for_arch(self.arch.name) and self.vendor.use_linux_image_cloud:
            self.classes.add('LINUX_IMAGE_CLOUD')
        else:
            self.classes.add('LINUX_IMAGE_BASE')
        self.classes.add('LAST')


class BuildCommand(BaseCommand):
    argparser_name = 'build'
    argparser_help = 'build Debian images'
    argparser_usage = '%(prog)s'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            'release',
            action=argparse_ext.ActionEnum,
            enum=ReleaseEnum,
            help='Debian release to build',
            metavar='RELEASE',
        )
        parser.add_argument(
            'vendor',
            action=argparse_ext.ActionEnum,
            enum=VendorEnum,
            help='Vendor to build image for',
            metavar='VENDOR',
        )
        parser.add_argument(
            'arch',
            action=argparse_ext.ActionEnum,
            enum=ArchEnum,
            help='Architecture or sub-architecture to build image for',
            metavar='ARCH',
        )
        parser.add_argument(
            '--build-id',
            metavar='ID',
            required=True,
            type=BuildId,
        )
        parser.add_argument(
            '--build-type',
            action=argparse_ext.ActionEnum,
            enum=BuildTypeEnum,
            default='dev',
            help='Type of image to build',
            metavar='TYPE',
        )
        parser.add_argument(
            '--noop',
            action='store_true',
            help='print the commands which would be executed, but do not run them'
        )
        parser.add_argument(
            '--localdebs',
            action='store_true',
            help='Read extra debs from localdebs directory',
        )
        parser.add_argument(
            '--output',
            default='.',
            help='write manifests and images to (default: .)',
            metavar='DIR',
            type=pathlib.Path
        )
        parser.add_argument(
            '--override-name',
            help='override name of output',
        )
        parser.add_argument(
            '--version',
            action=argparse_ext.ActionEnv,
            env='CI_PIPELINE_IID',
            help='version of image',
            metavar='VERSION',
            type=int,
        )
        parser.add_argument(
            '--version-date',
            default=datetime.now(),
            help='date part of version (default: today)',
            type=cls._argparse_type_date,
        )

    @staticmethod
    def _argparse_type_date(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            msg = "Given date ({0}) is not valid. Expected format: 'YYYY-MM-DD'".format(s)
            raise argparse.ArgumentTypeError(msg)

    def __init__(self, *, release=None, vendor=None, arch=None, version=None, build_id=None, build_type=None, localdebs=False, output=None, noop=False, override_name=None, version_date=None, **kw):
        super().__init__(**kw)

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

        self.env = self.c.env
        self.env['CLOUD_BUILD_INFO'] = json.dumps(self.c.info)
        self.env['CLOUD_BUILD_NAME'] = name
        self.env['CLOUD_BUILD_OUTPUT_DIR'] = output.resolve()
        self.env['CLOUD_BUILD_DATA'] = data_path

        output.mkdir(parents=True, exist_ok=True)

        image_raw = output / '{}.raw'.format(name)
        image_tar = output / '{}.tar'.format(name)
        manifest_fai = output / '{}.build-fai.json'.format(name)
        manifest_final = output / '{}.build.json'.format(name)

        self.fai = RunFAI(
            output_filename=image_raw,
            classes=self.c.classes,
            size_gb=self.c.vendor.fai_size,
            env=self.env,
        )

        self.tar = RunTar(
            input_filename=image_raw,
            output_filename=image_tar,
        )

        self.manifest = CreateManifest(
            input_filename=manifest_fai,
            output_filename=manifest_final,
            info=self.c.info,
        )

    def __call__(self):
        self.fai(not self.noop)
        digest = self.tar(not self.noop)
        self.manifest(not self.noop, (digest,))


if __name__ == '__main__':
    BuildCommand._main()
