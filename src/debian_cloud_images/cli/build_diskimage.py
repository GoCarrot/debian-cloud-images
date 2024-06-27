# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import logging
import struct
from pathlib import Path
from subprocess import CalledProcessError
from uuid import uuid4

from .base import cli, cli_internal, BaseCommand

from ..utils import sandbox
from ..utils.partition import Partition, PartitionEntry, PartitionType
from ..utils.oci_image import OciImage


logger = logging.getLogger()


@cli_internal.register(
    'build-diskimage',
    help='build Debian images',
    arguments=[
        cli.prepare_argument(
            'output',
            help='Directory to build a disk image',
            metavar='OUTPUT',
            type=Path
        ),
    ],
)
class BuildDiskimageCommand(BaseCommand):
    output: Path
    oci: OciImage

    def __init__(
        self, *,
        output: Path,
        **kw
    ) -> None:
        super().__init__(**kw)

        self.output = output
        self.oci = OciImage(output)

    def copy_part_root(self, input_tar: Path, part: PartitionEntry, fsuuid: str) -> None:
        output_tmp = self.output / 'tmp'
        output_raw = output_tmp / 'diskimage.data.root.raw'
        output_raw.unlink(missing_ok=True)

        logger.info(f'Create filesystem for partition type "root" and filesystem uuid {fsuuid}')

        with output_raw.open('wb') as f:
            f.truncate(part.size)

        input_tar_relative = input_tar.relative_to(self.output)

        script = f'''
        set -euE
        mkfs.ext4 -U {fsuuid} -d /input/{input_tar_relative!s} /output/{output_raw.name}
        '''

        try:
            sandbox.run_shell(
                script,
                bindmounts=[
                    (self.output.resolve(), Path('/input'), False),
                    (output_tmp.resolve(), Path('/output'), True),
                ],
                env={
                    'LC_ALL': 'C.UTF-8',
                },
            )

            with output_raw.open('rb') as f:
                part.copy_in(f)

        except CalledProcessError:
            output_raw.unlink()
            raise

    def copy_part_efi(self, input_tar: Path, part: PartitionEntry) -> None:
        output_tmp = self.output / 'tmp'
        output_raw = output_tmp / 'diskimage.data.efi.raw'
        output_raw.unlink(missing_ok=True)

        logger.info('Create filesystem for partition type "efi"')

        with output_raw.open('wb') as f:
            f.truncate(part.size)

        input_tar_relative = input_tar.relative_to(self.output)

        script = f'''
        set -euE
        tar --directory=/target --extract --file /input/{input_tar_relative!s} .
        mkfs.vfat /output/{output_raw.name}
        mcopy -s -p -Q -m -i /output/{output_raw.name} /target/boot/efi/* ::
        '''

        try:
            sandbox.run_shell(
                script,
                bindmounts=[
                    (self.output.resolve(), Path('/input'), False),
                    (output_tmp.resolve(), Path('/output'), True),
                ],
                env={
                    'LC_ALL': 'C.UTF-8',
                },
            )

            with output_raw.open('rb') as f:
                part.copy_in(f)

        except CalledProcessError:
            output_raw.unlink()
            raise

    def copy_grub_x86(self, input_tar: Path, part_bios_boot: PartitionEntry, part: Partition) -> None:
        output_tmp = self.output / 'tmp'
        output_out_boot = output_tmp / 'diskimage.data.grub.boot.img'
        output_out_core = output_tmp / 'diskimage.data.grub.core.img'
        output_out_boot.unlink(missing_ok=True)
        output_out_core.unlink(missing_ok=True)

        logger.info('Extract grub boot files')

        input_tar_relative = input_tar.relative_to(self.output)

        script = f'''
        set -euE
        tar --directory=/target --extract --file /input/{input_tar_relative!s} ./boot/grub/i386-pc/boot.img ./boot/grub/i386-pc/core.img
        mv /target/boot/grub/i386-pc/boot.img /output/{output_out_boot.name}
        mv /target/boot/grub/i386-pc/core.img /output/{output_out_core.name}
        '''

        try:
            sandbox.run_shell(
                script,
                bindmounts=[
                    (self.output.resolve(), Path('/input'), False),
                    (output_tmp.resolve(), Path('/output'), True),
                ],
                env={
                    'LC_ALL': 'C.UTF-8',
                },
            )

        except CalledProcessError:
            output_out_boot.unlink()
            output_out_core.unlink()
            raise

        with output_out_boot.open('rb') as f:
            # We only need the first 440 bytes of the boot.img, rest is partition table and magic
            boot_img = bytearray(f.read(440))

        with output_out_core.open('rb') as f:
            core_img = bytearray(f.read(3 * 1024 * 1024))

        # Patch absolute location of core.img start into boot.img
        GRUB_BOOT_MACHINE_KERNEL_SECTOR = 0x5c
        boot_img[GRUB_BOOT_MACHINE_KERNEL_SECTOR:GRUB_BOOT_MACHINE_KERNEL_SECTOR + 4] = \
            struct.pack('<L', part_bios_boot.start_sector)

        # Original comment:
        # FIXME: can this be skipped?
        GRUB_BOOT_MACHINE_BOOT_DRIVE = 0x64
        boot_img[GRUB_BOOT_MACHINE_BOOT_DRIVE] = 0xff

        # Original comment:
        # If DEST_DRIVE is a hard disk, enable the workaround, which is
        # for buggy BIOSes which don't pass boot drive correctly. Instead,
        # they pass 0x00 or 0x01 even when booted from 0x80.
        GRUB_BOOT_MACHINE_DRIVE_CHECK = 0x66
        boot_img[GRUB_BOOT_MACHINE_DRIVE_CHECK] = 0x90
        boot_img[GRUB_BOOT_MACHINE_DRIVE_CHECK + 1] = 0x90

        logger.info('Writing grub boot.img')
        with part.file.open('rb+') as f:
            f.seek(0)
            f.write(boot_img)

        # Patch absolute location of remaining core.img into start of itself
        GRUB_BOOT_MACHINE_LIST_SIZE = 12
        GRUB_BOOT_MACHINE_LIST_OFFSET = 0x200 - GRUB_BOOT_MACHINE_LIST_SIZE
        core_img[GRUB_BOOT_MACHINE_LIST_OFFSET:GRUB_BOOT_MACHINE_LIST_OFFSET + 8] = \
            struct.pack('<Q', part_bios_boot.start_sector + 1)

        logger.info('Writing grub core.img')
        part_bios_boot.copy_in_bytes(core_img)

    def do_manifest(self, manifest: dict) -> None:
        output_raw = self.output / 'tmp' / 'diskimage.data.full.raw'
        output_raw.unlink(missing_ok=True)

        part_root_path: Path | None = None
        part_efi_path: Path | None = None

        for layer in manifest['layers']:
            a = layer['annotations']
            if not layer['mediaType'] in (
                'application/vnd.oci.image.layer.v1.tar',
                'application/vnd.oci.image.layer.v1.tar+zstd',
            ):
                logger.info('Ignore layer, no tar')
            elif part_type := a.get('org.debian.cloud.images.internal.part.type', None):
                logger.info(f'Found layer with partition type "{part_type}"')

                if part_type == 'root':
                    part_root_partuuid = a['org.debian.cloud.images.internal.part.uuid']
                    part_root_fsuuid = a['org.debian.cloud.images.internal.part.fs.uuid']
                    part_root_path = self.oci.path_blob(layer['digest'])
                elif part_type == 'efi':
                    part_efi_partuuid = a['org.debian.cloud.images.internal.part.uuid']
                    part_efi_path = self.oci.path_blob(layer['digest'])
                else:
                    logger.info('Ignore layer, wrong partition type')
            else:
                logger.info('Ignore layer, no partition type annotation')

        # TODO, size
        part = Partition(output_raw, 2 * 1024 * 1024 * 1024)
        part_bios_boot = part.add(
            PartitionType.BOOT_AMD64,
            uuid4(),
            nr=14,
            size=3 * 1024 * 1024,
        )
        part_efi = part.add(
            PartitionType.ESP,
            part_efi_partuuid,
            nr=15,
            size=124 * 1024 * 1024,
        )
        part_root = part.add(
            PartitionType.ROOT_AMD64,
            part_root_partuuid,
            nr=1,
        )

        logger.info('Create partition table')
        part.write()

        assert part_bios_boot is not None
        assert part_root_path is not None
        assert part_efi_path is not None
        self.copy_grub_x86(part_root_path, part_bios_boot, part)
        self.copy_part_root(part_root_path, part_root, part_root_fsuuid)
        self.copy_part_efi(part_efi_path, part_efi)

    def __call__(self) -> None:
        oci = OciImage(self.output)

        index = oci.get_index()

        assert isinstance(index['manifests'], list)
        for manifest_info in index['manifests']:
            if (type_ := manifest_info['mediaType']) != 'application/vnd.oci.image.manifest.v1+json':
                logger.info(f'Ignoring manifest, unsupported type "{type_}"')
                continue

            digest = manifest_info['digest']
            manifest = oci.get_blob(digest)
            if (type_ := manifest['mediaType']) != 'application/vnd.oci.image.manifest.v1+json':
                logger.info(f'Ignoring manifest, unsupported type "{type_}"')
                continue

            logger.info(f'Use manifest {digest}')
            self.do_manifest(manifest)

            logger.info('Finished creating of disk image')


if __name__ == '__main__':
    cli.main(BuildDiskimageCommand)
