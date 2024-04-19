# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import pathlib


class TestBootFiles:
    @pytest.mark.parametrize('path', [
        '/boot/initrd.img*',
        '/boot/vmlinu[xz]*',
        '/boot/grub/grub.cfg',
    ])
    def test_boot_files(self, image_path, path):
        path = pathlib.Path(path)
        p = (image_path / path.relative_to('/'))
        assert len(list(p.parent.glob(p.name))) > 0, 'No files matching {}'.format(path)

    def check_dir_exist(self, image_path, path):
        path = pathlib.Path(path)
        p = (image_path / path.relative_to('/'))
        assert p.is_dir(), f'{path} does not exist'

    @pytest.mark.build_arch('arm64')
    def test_boot_grub_arm64_efi(self, image_path):
        self.check_dir_exist(image_path, '/boot/grub/arm64-efi')

    @pytest.mark.build_arch('amd64')
    def test_boot_grub_i386_pc(self, image_path):
        self.check_dir_exist(image_path, '/boot/grub/i386-pc')

    @pytest.mark.build_arch('ppc64el')
    def test_boot_grub_powerpc_ieee1275(self, image_path):
        self.check_dir_exist(image_path, '/boot/grub/powerpc-ieee1275')

    @pytest.mark.build_arch('riscv64')
    def test_boot_grub_riscv64_efi(self, image_path):
        self.check_dir_exist(image_path, '/boot/grub/riscv64-efi')

    @pytest.mark.build_arch('amd64')
    def test_boot_grub_x86_64_efi(self, image_path):
        self.check_dir_exist(image_path, '/boot/grub/x86_64-efi')
