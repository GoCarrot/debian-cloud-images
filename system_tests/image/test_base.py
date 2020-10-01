import pytest

import pathlib


class TestBase:
    @pytest.mark.parametrize('path', [
        '/proc',
        '/run',
        '/sys',
        '/tmp',
        '/var/cache/apt',
        '/var/lib/apt/lists',
        '/var/tmp',
    ])
    def test_dir_empty(self, image_path, path):
        path = pathlib.Path(path)
        p = (image_path / path.relative_to('/'))
        assert p.exists(), '{} does not exist'.format(path.as_posix())
        assert p.is_dir(), '{} is no directory'.format(path.as_posix())

        c = set(i.relative_to(p).as_posix() for i in p.glob('*'))
        assert len(c) == 0, '{} contains unexpected files: {}'.format(path.as_posix(), ', '.join(c))

    @pytest.mark.parametrize('path', [
        '/etc/mailname',
        '/initrd.img',
        '/vmlinux',
        '/vmlinuz',
    ])
    def test_file_absent(self, image_path, path):
        path = pathlib.Path(path)
        p = (image_path / path.relative_to('/'))
        assert not p.exists(), '{} exists'.format(path.as_posix())
