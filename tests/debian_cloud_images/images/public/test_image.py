import io
import json
import pytest

from unittest.mock import Mock

from debian_cloud_images.images.public.image import Image


def test_contextmanager_commit(tmp_path):
    image = Image(tmp_path, '/', 'image')
    image._commit = Mock()
    image._rollback = Mock()

    with image:
        pass

    image._commit.assert_called_once()
    image._rollback.assert_not_called()


def test_contextmanager_commit_exception(tmp_path):
    image = Image(tmp_path, '/', 'image')
    image._commit = Mock(side_effect=RuntimeError)
    image._rollback = Mock()

    with pytest.raises(RuntimeError):
        with image:
            pass

    image._commit.assert_called_once()
    image._rollback.assert_called_once()


def test_contextmanager_rollback(tmp_path):
    image = Image(tmp_path, '/', 'image')
    image._commit = Mock(side_effect=Exception)
    image._rollback = Mock()

    with pytest.raises(RuntimeError):
        with image:
            raise RuntimeError

    image._commit.assert_not_called()
    image._rollback.assert_called_once()


def test_contextmanager_output_exception(tmp_path):
    with pytest.raises(RuntimeError):
        with Image(tmp_path, '/', 'image'):
            raise RuntimeError


def test_contextmanager_output_success(tmp_path):
    with Image(tmp_path, '/', 'image'):
        pass
