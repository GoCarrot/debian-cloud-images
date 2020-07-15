import pytest

from unittest.mock import Mock, patch

from debian_cloud_images.images.public.version import Version


def test_contextmanager_commit(tmp_path):
    version = Version(tmp_path, '/', 'version')
    version._commit = Mock()
    version._rollback = Mock()

    with version:
        pass

    version._commit.assert_called_once()
    version._rollback.assert_not_called()


def test_contextmanager_commit_exception(tmp_path):
    version = Version(tmp_path, '/', 'version')
    version._commit = Mock(side_effect=RuntimeError)
    version._rollback = Mock()

    with pytest.raises(RuntimeError):
        with version:
            pass

    version._commit.assert_called_once()
    version._rollback.assert_called_once()


def test_contextmanager_rollback(tmp_path):
    version = Version(tmp_path, '/', 'version')
    version._commit = Mock(side_effect=Exception)
    version._rollback = Mock()

    with pytest.raises(RuntimeError):
        with version:
            raise RuntimeError

    version._commit.assert_not_called()
    version._rollback.assert_called_once()


def test_contextmanager_output_exception(tmp_path):
    with pytest.raises(RuntimeError):
        with Version(tmp_path, '/', 'version'):
            raise RuntimeError

    assert list(tmp_path.iterdir()) == []


def test_contextmanager_output_success(tmp_path):
    with Version(tmp_path, '/', 'version'):
        pass

    tmp_path_version = tmp_path / 'version'
    tmp_path_version_sha512 = tmp_path_version / 'SHA512SUMS'
    assert list(tmp_path.iterdir()) == [tmp_path_version]
    assert list(tmp_path_version.iterdir()) == [tmp_path_version_sha512]


def test_add_image(tmp_path):
    with patch('debian_cloud_images.images.public.version.Image', autospec=True) as mock:
        # autospec can't generate member variables
        mock.return_value.files = {}

        with Version(tmp_path, '/', 'version') as version:
            assert version.add_image('image', 'provider') is mock.return_value
            assert mock.call_args[0][1:] == ('/version/', 'image', 'provider')
