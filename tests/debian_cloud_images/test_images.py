import io
import json
import os
import pathlib
import pkg_resources
import pytest
import shutil
import tarfile

from debian_cloud_images.images import Images, Image


if pkg_resources.parse_version(pytest.__version__) < pkg_resources.parse_version('3.9'):
    # XXX: New in 3.9
    @pytest.fixture
    def tmp_path(tmpdir):
        return pathlib.Path(tmpdir.dirname)


check_no_qemu_img = shutil.which('qemu-img') is None
skip_no_qemu_img = pytest.mark.skipif(check_no_qemu_img,
                                      reason='Need available qemu-img')


@pytest.fixture
def images_path(tmp_path):
    with tmp_path.joinpath("test.build.json").open('w') as f:
        json.dump({
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'Build',
            'metadata': {
                'uid': '00000000-0000-0000-0000-000000000000',
            },
            'data': {
                'info': {
                    'arch': 'amd64',
                    'release': 'sid',
                    'release_id': 'sid',
                    'vendor': 'azure',
                    'version': '1',
                },
            },
        }, f)

    with tmp_path.joinpath("test.upload.json").open('w') as f:
        json.dump({
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'Upload',
            'metadata': {
                'uid': '00000000-0000-0000-0000-000000000001',
            },
            'data': {
                'provider': '',
                'ref': '',
            },
        }, f)

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
    images.read(images_path / 'test.build.json')
    images.read(images_path / 'test.upload.json')
    assert len(images) == 1


def test_Image(images_path):
    image = Image('test', images_path)
    image.read_manifests(images_path / 'test.build.json')
    image.read_manifests(images_path / 'test.upload.json')
    assert image.build_arch == 'amd64'

    with pytest.raises(RuntimeError):
        image.open_tar()


@skip_no_qemu_img
def test_Image_open_image(images_path_tar):
    images = Images()
    images.read(images_path_tar / 'test.build.json')
    image = images['test']

    with image.open_image('qcow2') as f:
        assert f.read(8) == b'QFI\xfb\0\0\0\3'

    with image.open_image('vhd') as f:
        assert f.read(8) == b'1' * 8
        f.seek(-512, os.SEEK_END)
        assert f.read(16) == b'conectix\0\0\0\2\0\1\0\0'

    with image.open_image('vmdk') as f:
        assert f.read(8) == b'KDMV\3\0\0\0'


def test_Image_open_tar(images_path_tar):
    images = Images()
    images.read(images_path_tar / 'test.build.json')
    image = images['test']
    with image.open_tar() as f:
        assert f


def test_Image_open_tar_xz(images_path_tar_xz):
    images = Images()
    images.read(images_path_tar_xz / 'test.build.json')
    image = images['test']
    with image.open_tar() as f:
        assert f
