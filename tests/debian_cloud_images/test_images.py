import io
import json
import pathlib
import pkg_resources
import pytest
import tarfile

from debian_cloud_images.images import Images


if pkg_resources.parse_version(pytest.__version__) < pkg_resources.parse_version('3.9'):
    # XXX: New in 3.9
    @pytest.fixture
    def tmp_path(tmpdir):
        return pathlib.Path(tmpdir.dirname)


@pytest.fixture
def images_path(tmp_path):
    with tmp_path.joinpath("test.json").open('w') as build:
        json.dump(
            {
                '_meta': {
                    'name': 'test',
                    'stage': 'build',
                },
                'build_info': {
                    'arch': 'amd64',
                    'image_type': 'vhd',
                    'release': 'sid',
                    'release_id': 'sid',
                    'vendor': 'azure',
                },
                'cloud_release': {},
            },
            build,
        )

    return tmp_path


@pytest.fixture
def images_path_tar(images_path):
    with images_path.joinpath('test.tar').open('wb') as f:
        with tarfile.open(fileobj=f, mode='x:') as tar:
            info = tarfile.TarInfo(name='disk.raw')
            info.size = 1024 * 1024
            tar.addfile(info, io.BytesIO(b'1' * 1024 * 1024))

    return images_path


@pytest.fixture
def images_path_tar_xz(images_path):
    with images_path.joinpath('test.tar.xz').open('wb') as f:
        with tarfile.open(fileobj=f, mode='x:xz') as tar:
            info = tarfile.TarInfo(name='disk.raw')
            info.size = 1024 * 1024
            tar.addfile(info, io.BytesIO(b'1' * 1024 * 1024))

    return images_path


def test_Images(images_path):
    images = Images()
    images.read_path(images_path)
    assert len(images) == 1


def test_Image(images_path):
    images = Images()
    images.read_path(images_path)
    image = images['test']
    assert image.build_arch == 'amd64'

    with pytest.raises(RuntimeError):
        image.get_tar()


def test_Image_get_tar(images_path_tar):
    images = Images()
    images.read_path(images_path_tar)
    image = images['test']
    assert image.get_tar()


def test_Image_get_tar_xz(images_path_tar_xz):
    images = Images()
    images.read_path(images_path_tar_xz)
    image = images['test']
    assert image.get_tar()
