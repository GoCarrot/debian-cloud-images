import pytest

from unittest.mock import Mock, patch

from debian_cloud_images.images.public.release import Release


def test_contextmanager_commit(tmp_path):
    release = Release(tmp_path, '/', 'release', 'release')
    release._commit = Mock()
    release._rollback = Mock()

    with release:
        pass

    release._commit.assert_called_once()
    release._rollback.assert_not_called()


def test_contextmanager_commit_exception(tmp_path):
    release = Release(tmp_path, '/', 'release', 'release')
    release._commit = Mock(side_effect=RuntimeError)
    release._rollback = Mock()

    with pytest.raises(RuntimeError):
        with release:
            pass

    release._commit.assert_called_once()
    release._rollback.assert_called_once()


def test_contextmanager_rollback(tmp_path):
    release = Release(tmp_path, '/', 'release', 'release')
    release._commit = Mock(side_effect=Exception)
    release._rollback = Mock()

    with pytest.raises(RuntimeError):
        with release:
            raise RuntimeError

    release._commit.assert_not_called()
    release._rollback.assert_called_once()


def test_contextmanager_output_exception_release(tmp_path):
    with pytest.raises(RuntimeError):
        with Release(tmp_path, '/', 'release', 'release'):
            raise RuntimeError

    tmp_path_release = tmp_path / 'release'
    assert list(tmp_path.iterdir()) == [tmp_path_release]
    assert list(tmp_path_release.iterdir()) == []


def test_contextmanager_output_exception_unknown(tmp_path):
    with pytest.raises(RuntimeError):
        with Release(tmp_path, '/', 'release', 'type'):
            raise RuntimeError

    tmp_path_release = tmp_path / 'release'
    tmp_path_type = tmp_path_release / 'type'
    assert list(tmp_path.iterdir()) == [tmp_path_release]
    assert list(tmp_path_release.iterdir()) == [tmp_path_type]
    assert list(tmp_path_type.iterdir()) == []


def test_contextmanager_output_success_release(tmp_path):
    with Release(tmp_path, '/', 'release', 'release'):
        pass

    tmp_path_release = tmp_path / 'release'
    assert list(tmp_path.iterdir()) == [tmp_path_release]
    assert list(tmp_path_release.iterdir()) == []


def test_contextmanager_output_success_unknown(tmp_path):
    with Release(tmp_path, '/', 'release', 'type'):
        pass

    tmp_path_release = tmp_path / 'release'
    tmp_path_type = tmp_path_release / 'type'
    assert list(tmp_path.iterdir()) == [tmp_path_release]
    assert list(tmp_path_release.iterdir()) == [tmp_path_type]
    assert list(tmp_path_type.iterdir()) == []


def test_add_version(tmp_path):
    with patch('debian_cloud_images.images.public.release.Version', autospec=True) as mock:
        with Release(tmp_path, '/', 'release', 'type') as release:
            assert release.add_version('version') is mock.return_value
            mock.assert_called_with(tmp_path / 'release' / 'type', '/release/type/', 'version')
