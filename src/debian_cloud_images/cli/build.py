import collections.abc
import enum
import json
import logging
import os
import pathlib
import re
import subprocess

from .base import BaseCommand

from ..build import fai_config_path
from ..utils import argparse_ext


logger = logging.getLogger()


class Arch:
    def __init__(self, kw):
        def init(*, fai_classes):
            self.fai_classes = fai_classes
        init(**kw)


class Release:
    def __init__(self, kw):
        def init(*, id, fai_classes, supports_linux_image_cloud=False):
            self.id = id
            self.fai_classes = fai_classes
            self.supports_linux_image_cloud = supports_linux_image_cloud
        init(**kw)


class Vendor:
    def __init__(self, kw):
        def init(*, fai_size, fai_classes, use_linux_image_cloud=False):
            self.fai_size = fai_size
            self.fai_classes = fai_classes
            self.use_linux_image_cloud = use_linux_image_cloud
        init(**kw)


class BuildType:
    def __init__(self, kw):
        def init(*, fai_classes, require_release=False):
            self.fai_classes = fai_classes
            self.require_release = require_release
        init(**kw)


ArchEnum = enum.Enum(
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


ReleaseEnum = enum.Enum(
    'ReleaseEnum',
    {
        'stretch': {
            'id': '9',
            'fai_classes': ('STRETCH', 'BACKPORTS'),
        },
        'stretch-backports': {
            'id': '9-backports',
            'fai_classes': ('STRETCH', 'BACKPORTS', 'BACKPORTS_LINUX'),
            'supports_linux_image_cloud': True,
        },
        'buster': {
            'id': '10',
            'fai_classes': ('BUSTER', ),
            'supports_linux_image_cloud': True,
        },
        'sid': {
            'id': 'sid',
            'fai_classes': ('SID', ),
            'supports_linux_image_cloud': True,
        },
    },
    type=Release,
)


VendorEnum = enum.Enum(
    'VendorEnum',
    {
        'azure': {
            'fai_size': '30G',
            'fai_classes': ('AZURE', ),
            'use_linux_image_cloud': True,
        },
        'ec2': {
            'fai_size': '8G',
            'fai_classes': ('EC2', ),
        },
        'gce': {
            'fai_size': '10G',
            'fai_classes': ('GCE', ),
            'use_linux_image_cloud': True,
        },
        'nocloud': {
            'fai_size': '8G',
            'fai_classes': ('NOCLOUD', ),
        },
        'openstack': {
            'fai_size': '2G',
            'fai_classes': ('OPENSTACK', ),
        },
    },
    type=Vendor,
)


BuildTypeEnum = enum.Enum(
    'BuildTypeEnum',
    {
        'dev': {
            'fai_classes': ('TYPE_DEV', ),
        },
        'official': {
            'fai_classes': (),
            'require_release': True,
        },
    },
    type=BuildType,
)


class BuildId:
    re = re.compile(r"^(?P<release>\d{8})|[a-z][a-z0-9-]+$")

    def __init__(self, s):
        r = self.re.match(s)

        if not r:
            raise ValueError('invalid build id value')

        self.id = r.group(0)
        self.release = r.group('release')


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
        self.classes |= self.release.fai_classes

    def set_vendor(self, vendor):
        self.vendor = vendor
        self.info['vendor'] = self.vendor.name
        self.classes |= self.vendor.fai_classes

    def set_arch(self, arch):
        self.arch = arch
        self.info['arch'] = self.arch.name
        self.classes |= self.arch.fai_classes

    def set_version(self, build_id, ci_pipeline_iid):
        if self.type.require_release and not build_id.release:
            raise ValueError('need release build id for selected build type')

        self.version = '{!s}-{!s}'.format(build_id.id, ci_pipeline_iid)
        self.env['CLOUD_RELEASE_VERSION'] = self.info['version'] = self.version
        if self.vendor.name == 'azure':
            self.env['CLOUD_RELEASE_VERSION_AZURE'] = self.info['version_azure'] = '0.{!s}.{!s}'.format(build_id.release or 0, ci_pipeline_iid)

    def check(self):
        if self.release.supports_linux_image_cloud and self.vendor.use_linux_image_cloud:
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
            '--ci-pipeline-iid',
            action=argparse_ext.ActionEnv,
            env='CI_PIPELINE_IID',
            metavar='ID',
            type=int,
        )
        parser.add_argument(
            '--build-type',
            action=argparse_ext.ActionEnum,
            enum=BuildTypeEnum,
            default='dev',
            help='Type of image to build',
            metavar='TYPE',
        )
        parser.add_argument('--noop', action='store_true')
        parser.add_argument(
            '--localdebs',
            action='store_true',
            help='Read extra debs from localdebs directory',
        )
        parser.add_argument(
            '--path',
            default='.',
            help='write manifests and images to (default: .)',
            metavar='PATH',
            type=pathlib.Path
        )
        parser.add_argument(
            '--override-name',
            help='override name of output',
        )

    def __init__(self, *, release=None, vendor=None, arch=None, build_id=None, ci_pipeline_iid=None, build_type=None, localdebs=False, path=None, noop=False, override_name=None, **kw):
        super().__init__(**kw)

        self.noop = noop

        self.c = Check()
        self.c.set_type(build_type)
        self.c.set_release(release)
        self.c.set_vendor(vendor)
        self.c.set_arch(arch)
        self.c.set_version(build_id, ci_pipeline_iid)
        if localdebs:
            self.c.classes.add('LOCALDEBS')
        self.c.check()

        name = override_name or 'debian-{release}-{vendor}-{arch}-{build_type}-{version}'.format(
            build_type=self.c.type.name,
            release=self.c.release.name,
            vendor=self.c.vendor.name,
            arch=self.c.arch.name,
            version=self.c.version,
        )

        self.env = os.environ.copy()
        self.env.update(self.c.env)
        self.env['CLOUD_BUILD_INFO'] = json.dumps(self.c.info)
        self.env['CLOUD_BUILD_NAME'] = name
        self.env['CLOUD_BUILD_OUTPUT_DIR'] = path.resolve()

        image_raw = path / '{}.raw'.format(name)
        image_tar = path / '{}.tar'.format(name)

        self.cmd = (
            'fai-diskimage',
            '--verbose',
            '--hostname', 'debian',
            '--class', ','.join(self.c.classes),
            '--size', self.c.vendor.fai_size,
            '--cspace', fai_config_path,
            image_raw.as_posix(),
        )

        self.cmd_tar = (
            'tar',
            '-cS',
            '-f', image_tar.as_posix(),
            '--transform', r'flags=r;s|.*\.raw|disk.raw|',
            image_raw.as_posix(),
        )

    def __call__(self):
        logging.info('Running: %s; %s', ' '.join(self.cmd), ' '.join(self.cmd_tar))

        if not self.noop:
            subprocess.check_call(self.cmd, env=self.env)
            subprocess.check_call(self.cmd_tar)


if __name__ == '__main__':
    parser = BuildCommand._argparse_init_base()

    args = parser.parse_args()
    BuildCommand(**vars(args))()
