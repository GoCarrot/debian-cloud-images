import pytest

from debian_cloud_images.resources import open_text, path


def test_open_text():
    open_text('image.yaml')


def test_open_text_dir():
    with pytest.raises(IsADirectoryError):
        open_text('system_tests')


def test_open_text_nonexistent():
    with pytest.raises(FileNotFoundError):
        open_text('nonexistent')


def test_path_dir():
    with path('system_tests') as p:
        assert p.name == 'system_tests'
        assert p.is_dir()


def test_path_file():
    with path('image.yaml') as p:
        assert p.name == 'image.yaml'
        assert p.is_file()


def test_path_nonexistent():
    with path('nonexistent') as p:
        assert p.name == 'nonexistent'
        assert not p.exists()
