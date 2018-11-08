import collections.abc
import enum
import logging
import os
import re
import subprocess

from .base import BaseCommand

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
        def init(*, fai_size, fai_classes, image_cls, use_linux_image_cloud=False):
            self.fai_size = fai_size
            self.fai_classes = fai_classes
            self.image = image_cls()
            self.use_linux_image_cloud = use_linux_image_cloud
        init(**kw)


class ImageType:
    def convert_image(self, basename):
        pass


class ImageTypeRaw(ImageType):
    NAME = 'raw'

    def convert_image(self, basename, noop):
        cmd = (
            'tar', '-cS',
            '-f', '{}.tar'.format(basename),
            '--transform', r'flags=r;s|.*\.raw|disk.raw|',
            '{}.raw'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)


class ImageTypeVhd(ImageType):
    NAME = 'vhd'

    def convert_image(self, basename, noop):
        cmd = (
            'qemu-img', 'convert',
            '-f', 'raw', '-o', 'subformat=fixed,force_size', '-O', 'vpc',
            '{}.raw'.format(basename), '{}.vhd'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)

        cmd = (
            'tar', '-cS',
            '-f', '{}.tar'.format(basename),
            '--transform', r'flags=r;s|.*\.vhd|disk.vhd|',
            '{}.vhd'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)


class ImageTypeQcow2(ImageType):
    NAME = 'qcow2'

    def convert_image(self, basename, noop):
        cmd = (
            'qemu-img', 'convert',
            '-f', 'raw', '{}.raw'.format(basename),
            '-o', 'compat=0.10',
            '-O', 'qcow2', '{}.qcow2'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)

        cmd = (
            'tar', '-cS',
            '-f', '{}.tar'.format(basename),
            '--transform', r'flags=r;s|.*\.qcow2|disk.qcow2|',
            '{}.qcow2'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)


class ImageTypeVmdk(ImageType):
    NAME = 'vmdk'

    def convert_image(self, basename, noop):
        cmd = (
            'qemu-img', 'convert',
            '-f', 'raw', '-O', 'vmdk', '-o', 'subformat=streamOptimized',
            '{}.raw'.format(basename), '{}.vmdk'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)

        cmd = (
            'tar', '-cS',
            '-f', '{}.tar'.format(basename),
            '--transform', r'flags=r;s|.*\.vmdk|disk.vmdk|',
            '{}.vmdk'.format(basename),
        )
        logging.info('Running: %s', ' '.join(cmd))

        if not noop:
            subprocess.check_call(cmd)


ArchEnum = enum.Enum(
    'ArchEnum',
    {
        'amd64': {
            'fai_classes': ('AMD64', 'GRUB_PC'),
        },
        'amd64-efi': {
            'fai_classes': ('AMD64', 'GRUB_EFI_AMD64'),
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
            'image_cls': ImageTypeVhd,
            'use_linux_image_cloud': True,
        },
        'ec2': {
            'fai_size': '8G',
            'fai_classes': ('EC2', ),
            'image_cls': ImageTypeVmdk,
        },
        'gce': {
            'fai_size': '10G',
            'fai_classes': ('GCE', ),
            'image_cls': ImageTypeRaw,
        },
        'nocloud': {
            'fai_size': '8G',
            'fai_classes': ('NOCLOUD', ),
            'image_cls': ImageTypeRaw,
        },
        'openstack': {
            'fai_size': '2G',
            'fai_classes': ('OPENSTACK', ),
            'image_cls': ImageTypeQcow2,
        },
    },
    type=Vendor,
)


class Version:
    re = re.compile(r"(?P<release>^(?P<release_base>\d{8})(?P<release_extra>[a-z])?$)|(^dev)")

    def __init__(self, s):
        r = self.re.match(s)

        self.release = r.group('release')
        self.release_base = r.group('release_base')
        self.release_extra = r.group('release_extra')


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

    def set_release(self, release):
        self.release = release
        self.env['CLOUD_BUILD_INFO_RELEASE'] = self.release.name
        self.env['CLOUD_BUILD_INFO_RELEASE_ID'] = self.release.id
        self.classes |= self.release.fai_classes

    def set_vendor(self, vendor):
        self.vendor = vendor
        self.env['CLOUD_BUILD_INFO_VENDOR'] = self.vendor.name
        self.env['CLOUD_BUILD_INFO_IMAGE_TYPE'] = self.vendor.image.NAME
        self.classes |= self.vendor.fai_classes

    def set_arch(self, arch):
        self.arch = arch
        self.env['CLOUD_BUILD_INFO_ARCH'] = self.arch.name
        self.classes |= self.arch.fai_classes

    def set_version(self, version):
        if version.release:
            self.env['CLOUD_RELEASE_VERSION'] = version.release

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
        parser.add_argument('name', metavar='NAME')
        parser.add_argument('version', metavar='VERSION', type=Version)
        parser.add_argument('--noop', action='store_true')

    def __init__(self, *, release=None, vendor=None, arch=None, version=None, name=None, noop=False, **kw):
        super().__init__(**kw)

        self.name = name
        self.noop = noop

        self.c = Check()
        self.c.set_release(release)
        self.c.set_vendor(vendor)
        self.c.set_arch(arch)
        self.c.set_version(version)
        self.c.check()

        self.env = os.environ.copy()
        self.env.update(self.c.env)
        self.env['CLOUD_BUILD_NAME'] = name
        self.env['CLOUD_BUILD_OUTPUT_DIR'] = os.getcwd()

        if os.path.isdir(os.path.join(os.getcwd(), 'config_space')):
            config_space_folder = os.path.join(os.getcwd(), 'config_space')
        else:
            config_space_folder = '/usr/share/debian-cloud-images/config_space'

        self.cmd = (
            'fai-diskimage',
            '--verbose',
            '--hostname', 'debian',
            '--class', ','.join(self.c.classes),
            '--size', self.c.vendor.fai_size,
            '--cspace', config_space_folder,
            name + '.raw',
        )

    def __call__(self):
        logging.info('Running: %s', ' '.join(self.cmd))

        if not self.noop:
            subprocess.check_call(self.cmd, env=self.env)

        self.c.vendor.image.convert_image(self.name, self.noop)


if __name__ == '__main__':
    parser = BuildCommand._argparse_init_base()

    args = parser.parse_args()
    BuildCommand(**vars(args))()
