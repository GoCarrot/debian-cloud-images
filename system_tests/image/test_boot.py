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
