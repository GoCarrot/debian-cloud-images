# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import collections.abc
import importlib.resources
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import (
    Optional,
)

from .base import cli, cli_internal, BaseCommand

from .. import resources
from ..build.manifest import CreateManifest
from ..utils import argparse_ext
from ..utils import sandbox
from ..utils.oci_image import OciImage


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


@cli_internal.register(
    'build-rootfs',
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
            type=Path
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
    def __init__(
        self, *,
        release_name: str,
        vendor_name: str,
        arch_name: str,
        version: int,
        build_id: BuildId,
        build_type_name: str,
        output: Path,
        localdebs: bool = False,
        noop: bool = False,
        override_name: Optional[str] = None,
        version_date: Optional[datetime] = None,
        **kw
    ) -> None:
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

        self.output = output
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

        self.name = override_name or self.c.type.output_name.format(
            build_type=self.c.type.name,
            release=self.c.release.name,
            vendor=self.c.vendor.name,
            arch=self.c.arch.name,
            version=self.c.version,
            build_id=self.c.build_id,
        )

        self.env = self.c.env
        self.env['LC_ALL'] = 'C'
        self.env['PATH'] = '/usr/bin:/usr/sbin'
        self.env['CLOUD_BUILD_NAME'] = 'rootfs'
        self.env['CLOUD_BUILD_OUTPUT_DIR'] = '/fai/output'

    def __call__(self) -> None:
        output_base = self.output / self.name
        output_tmp = output_base / 'tmp'
        output_tarzst_root = output_tmp / 'rootfs.data.root.tar.zst'
        output_tarzst_efi = output_tmp / 'rootfs.data.efi.tar.zst'
        output_log = output_tmp / 'log'
        output_dpkg_status = output_tmp / 'rootfs.dpkg-status'

        script = f'''
        set -euE
        fai -v -u localhost -s file:///fai/config -c '{','.join(self.c.classes)}' install /target
        tar --directory=/target --exclude ./boot/efi/* --create --sort=name --xattrs --xattrs-include='*' . | \\
          zstd -f -T0 -10 -o /fai/output/{output_tarzst_root.name}
        if [[ -d /target/boot/efi ]]; then
          tar --directory=/target --create --sort=name ./boot/efi | \\
            zstd -f -T0 -10 -o /fai/output/{output_tarzst_efi.name}
        fi
        '''

        oci = OciImage(output_base)

        with importlib.resources.as_file(
            importlib.resources.files(resources) / 'fai_config' / self.c.release.basename
        ) as p_fai_config:
            output_tmp.mkdir(parents=True, exist_ok=True)
            output_log.mkdir(parents=True, exist_ok=True)

            try:
                sandbox.run_shell(
                    script,
                    bindmounts=[
                        (p_fai_config.resolve(), Path('/fai/config'), False),
                        (output_tmp.resolve(), Path('/fai/output'), True),
                        (output_log.resolve(), Path('/var/log/fai'), True),
                    ],
                    env=self.env,
                )

            except CalledProcessError as e:
                sys.exit(e.returncode)

        info_manifest_digests: list[str] = []
        info_manifest_layers: list[dict] = []

        uuid_fs_root = (output_tmp / 'rootfs.data.root.fsuuid').open().read()
        uuid_part_root = (output_tmp / 'rootfs.data.root.partuuid').open().read()
        uuid_part_efi = (output_tmp / 'rootfs.data.efi.partuuid').open().read()

        layer = oci.store_blob_from_tmp(output_tarzst_root.name)
        info_manifest_digests.append(layer.digest)
        info_manifest_layers.append({
            'mediaType': 'application/vnd.oci.image.layer.v1.tar+zstd',
            'digest': layer.digest,
            'size': layer.size,
            'annotations': {
                'org.debian.cloud.images.internal.part.type': 'root',
                'org.debian.cloud.images.internal.part.uuid': uuid_part_root,
                'org.debian.cloud.images.internal.part.fs.uuid': uuid_fs_root,
            }
        })

        if output_tarzst_efi.exists():
            layer = oci.store_blob_from_tmp(output_tarzst_efi.name)
            info_manifest_digests.append(layer.digest)
            info_manifest_layers.append({
                'mediaType': 'application/vnd.oci.image.layer.v1.tar+zstd',
                'digest': layer.digest,
                'size': layer.size,
                'annotations': {
                    'org.debian.cloud.images.internal.part.type': 'efi',
                    'org.debian.cloud.images.internal.part.uuid': uuid_part_efi,
                }
            })

        info_oci_config = oci.store_blob({
            'architecture': self.c.arch.oci_arch,
            'os': 'linux',
            'config': {
                'Cmd': [
                    'bash'
                ],
                'Env': [
                    'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                ],
            },
            'rootfs': {
                'diff_ids': info_manifest_digests,
                'type': 'layers',
            },
        })

        info_oci_manifest = oci.store_blob({
            'schemaVersion': 2,
            'mediaType': 'application/vnd.oci.image.manifest.v1+json',
            'config': {
                'mediaType': 'application/vnd.oci.image.config.v1+json',
                'digest': info_oci_config.digest,
                'size': info_oci_config.size,
            },
            'layers': info_manifest_layers,
        })

        info_debian_config = oci.store_blob(CreateManifest(
            dpkg_status=output_dpkg_status,
            output_filename=None,
            info=self.c.info,
        )())

        info_debian_manifest = oci.store_blob({
            'schemaVersion': 2,
            'mediaType': 'application/vnd.debian.cloud.oci.image.manifest.v1+json',
            'config': {
                'mediaType': 'application/vnd.debian.cloud.oci.image.config.v1+json',
                'digest': info_debian_config.digest,
                'size': info_debian_config.size,
            },
            'layers': [],
        })

        oci.store_index({
            'schemaVersion': 2,
            'mediaType': 'application/vnd.oci.image.index.v1+json',
            'manifests': [
                {
                    'mediaType': 'application/vnd.oci.image.manifest.v1+json',
                    'digest': info_oci_manifest.digest,
                    'size': info_oci_manifest.size,
                    'annotations': {
                        'org.opencontainers.image.ref.name': 'oci',
                    },
                    'platform': {
                        'architecture': self.c.arch.oci_arch,
                        'os': 'linux'
                    },
                },
                {
                    'mediaType': 'application/vnd.debian.cloud.oci.image.manifest.v1+json',
                    'digest': info_debian_manifest.digest,
                    'size': info_debian_manifest.size,
                    'annotations': {
                        'org.opencontainers.image.ref.name': 'debian',
                    },
                    'platform': {
                        'architecture': self.c.arch.oci_arch,
                        'os': 'linux'
                    },
                },
            ],
        })


if __name__ == '__main__':
    cli.main(BuildCommand)
