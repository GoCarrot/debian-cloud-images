import pytest

import json
import pathlib

from debian_cloud_images.utils import argparse_ext


def pytest_addoption(parser):
    parser.addoption(
        '--mount-build-info',
        action=argparse_ext.ActionEnv,
        env='CLOUD_BUILD_INFO',
        metavar='JSON',
    )
    parser.addoption(
        '--mount-path',
        type=pathlib.Path,
    )


@pytest.fixture(scope="session")
def image_build_info(request):
    return json.loads(request.config.getoption('mount_build_info'))


@pytest.fixture(scope="session")
def image_path(request):
    return request.config.getoption('mount_path')
