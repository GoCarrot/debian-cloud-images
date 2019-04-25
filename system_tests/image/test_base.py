import pytest

import pathlib


class TestBase:
    @pytest.mark.parametrize('path', [
        '/tmp',
        '/var/tmp',
    ])
    def test_dir_empty(self, image_path, path):
        path = pathlib.Path(path)
        p = (image_path / path.relative_to('/'))
        assert p.exists(), '{} does not exist'.format(path.as_posix())
        assert p.is_dir(), '{} is no directory'.format(path.as_posix())
        assert len(list(p.glob('*'))) == 0, '{} is not empty'.format(path.as_posix())

    @pytest.mark.parametrize('path', [
        '/initrd.img',
        '/vmlinux',
        '/vmlinuz',
    ])
    def test_file_absent(self, image_path, path):
        path = pathlib.Path(path)
        p = (image_path / path.relative_to('/'))
        assert not p.exists(), '{} exists'.format(path.as_posix())
