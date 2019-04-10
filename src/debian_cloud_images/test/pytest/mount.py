import pytest

import json
import pathlib

from ...images import Image
from ...utils import argparse_ext


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
def image_info(request):
    build_info = request.config.getoption('mount_build_info')
    image = Image('default', '')
    image.build_info = json.loads(build_info)
    return image


@pytest.fixture(scope="session")
def image_path(request):
    return request.config.getoption('mount_path')
