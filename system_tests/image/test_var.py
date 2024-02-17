# SPDX-License-Identifier: GPL-2.0-or-later

class TestVar:
    def test_var_log(self, image_path):
        p = image_path / 'var' / 'log'
        assert p.exists(), '/var/log does not exist'
        assert p.is_dir(), '/var/log is no directory'

        c = set(i.relative_to(p).as_posix() for i in p.glob('*'))
        c.difference_update((
            'apt',
            'btmp',
            'chrony',
            'faillog',
            'journal',  # systemd persistent journal
            'lastlog',
            'private',
            'runit',
            'unattended-upgrades',
            'wtmp',
            'README',
        ))

        assert len(c) == 0, '/var/log contains unexpected files: {}'.format(', '.join(c))
