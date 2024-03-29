# SPDX-License-Identifier: GPL-2.0-or-later

import pytest


class TestEtc:
    def test_etc_cloud_release(self, image_path):
        assert (image_path / 'etc' / 'cloud-release').exists()

    def test_etc_default_locale(self, image_path):
        p = (image_path / 'etc' / 'default' / 'locale')
        assert p.exists(), '/etc/default/locale does not exist'

        with p.open() as f:
            assert f.read() == 'LANG=C.UTF-8\n', 'Default locale is not C.UTF-8'

    def test_etc_fstab(self, image_path):
        p = image_path / 'etc/fstab'
        assert p.is_file()
        assert not p.is_symlink()

    def test_etc_resolv_conf(self, image_path):
        p = image_path / 'etc' / 'resolv.conf'
        assert not p.exists() or p.is_symlink(), '/etc/resolv.conf does exist and is not a symlink'

    @pytest.mark.parametrize('name', [
        'root',
        'nogroup',
        # From cloud-init config
        'adm',
        'audio',
        'cdrom',
        'dialout',
        'dip',
        'floppy',
        'plugdev',
        'sudo',
        'video',
    ])
    def test_group_exist(self, image_etc_group, name):
        assert name in image_etc_group, f'/etc/group is missing group {name}'

    def test_group_name(self, image_etc_group_entry):
        name = image_etc_group_entry.name
        if name in (
            # From package base-passwd
            'root', 'daemon', 'bin', 'sys', 'adm', 'tty', 'disk', 'lp', 'mail',
            'news', 'uucp', 'man', 'proxy', 'kmem', 'dialout', 'fax', 'voice',
            'cdrom', 'floppy', 'tape', 'sudo', 'audio', 'dip', 'www-data',
            'backup', 'operator', 'list', 'irc', 'src', 'shadow', 'utmp',
            'video', 'sasl', 'plugdev', 'staff', 'games', 'users', 'nogroup',
            # From package dbus
            'messagebus',
            # From package polkit
            'polkitd',
            # From package tcpdump
            'tcpdump',
            # From package udev
            'input', 'kvm', 'render', 'sgx',
            # From package uuid-runtime
            'uuidd',
        ):
            return
        if name.startswith('_') or name.startswith('systemd-'):
            return
        pytest.fail('/etc/group includes group {} with not allowed name'.format(name), pytrace=False)

    def test_group_gid(self, image_etc_group_entry):
        name = image_etc_group_entry.name
        gid = int(image_etc_group_entry.gid)
        if gid >= 0 and gid < 1000:
            return
        if gid == 65534:
            return
        pytest.fail('/etc/group includes group {} with not allowed gid {}'.format(name, gid), pytrace=False)

    @pytest.mark.parametrize('name', [
        'root',
        'nobody',
    ])
    def test_passwd_exist(self, image_etc_passwd, name):
        assert name in image_etc_passwd, f'/etc/passwd is missing user {name}'

    def test_passwd_name(self, image_etc_passwd_entry):
        name = image_etc_passwd_entry.name
        if name in (
            # From package base-passwd
            'root', 'daemon', 'bin', 'sys', 'sync', 'games', 'man', 'lp',
            'mail', 'news', 'uucp', 'proxy', 'www-data', 'backup', 'list',
            'irc', 'gnats', 'nobody',
            # From package dbus
            'messagebus',
            # From package polkit
            'polkitd',
            # From package openssh-server
            'sshd',
            # From package tcpdump
            'tcpdump',
            # From package uuid-runtime
            'uuidd',
        ):
            return
        if name.startswith('_') or name.startswith('systemd-'):
            return
        pytest.fail('/etc/passwd includes user {} with not allowed name'.format(name), pytrace=False)

    def test_passwd_shell(self, image_etc_passwd_entry):
        name = image_etc_passwd_entry.name
        shell = image_etc_passwd_entry.shell
        if shell == '/bin/bash' and name == 'root':
            return
        if shell == '/bin/sync' and name == 'sync':
            return
        if shell in ('/bin/false', '/sbin/nologin', '/usr/sbin/nologin'):
            return
        pytest.fail('/etc/passwd includes user {} with not allowed shell {}'.format(name, shell), pytrace=False)

    def test_passwd_uid(self, image_etc_passwd_entry):
        name = image_etc_passwd_entry.name
        uid = int(image_etc_passwd_entry.uid)
        if uid >= 0 and uid < 1000:
            return
        if uid == 65534:
            return
        pytest.fail('/etc/passwd includes user {} with not allowed uid {}'.format(name, uid), pytrace=False)
