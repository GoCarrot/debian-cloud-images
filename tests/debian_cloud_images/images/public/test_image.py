import io
import json
import pytest
import tarfile

from unittest.mock import Mock

from debian_cloud_images.images.public.image import Image


@pytest.fixture
def image(tmp_path):
    from debian_cloud_images.images import Image

    f = Mock()
    f.open = Mock()
    f.open.return_value = io.StringIO(json.dumps({
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
    }))

    i = Image('input', tmp_path)
    i.read_manifests(f)

    return i


@pytest.fixture
def image_tar_path(tmp_path):
    with tmp_path.joinpath('input.tar').open('wb') as f:
        with tarfile.open(fileobj=f, mode='x:') as tar:
            info = tarfile.TarInfo(name='disk.raw')
            info.size = 0
            tar.addfile(info, io.BytesIO(b''))

    return tmp_path


def test_contextmanager_commit(tmp_path):
    image = Image(tmp_path, '/', 'image', 'provider')
    image._commit = Mock()
    image._rollback = Mock()

    with image:
        pass

    image._commit.assert_called_once()
    image._rollback.assert_not_called()


def test_contextmanager_commit_exception(tmp_path):
    image = Image(tmp_path, '/', 'image', 'provider')
    image._commit = Mock(side_effect=RuntimeError)
    image._rollback = Mock()

    with pytest.raises(RuntimeError):
        with image:
            pass

    image._commit.assert_called_once()
    image._rollback.assert_called_once()


def test_contextmanager_rollback(tmp_path):
    image = Image(tmp_path, '/', 'image', 'provider')
    image._commit = Mock(side_effect=Exception)
    image._rollback = Mock()

    with pytest.raises(RuntimeError):
        with image:
            raise RuntimeError

    image._commit.assert_not_called()
    image._rollback.assert_called_once()


def test_contextmanager_output_exception(tmp_path):
    with pytest.raises(RuntimeError):
        with Image(tmp_path, '/', 'image', 'provider'):
            raise RuntimeError


def test_contextmanager_output_success(tmp_path):
    with Image(tmp_path, '/', 'image', 'provider'):
        pass


def test_write(tmp_path, image, image_tar_path):
    with Image(tmp_path, '/', 'image', 'provider') as s:
        s.write(image, 'undefined')
        assert len(s.manifests) == 1

    assert sorted(list(i.name for i in tmp_path.iterdir())) == ['image.json', 'image.tar', 'input.tar']
