# SPDX-License-Identifier: GPL-2.0-or-later

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


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'build_arch(name): mark test to run only on named architecture'
    )


def pytest_runtest_setup(item):
    build_info = json.loads(item.config.getoption('mount_build_info'))

    if i := [mark.args[0] for mark in item.iter_markers(name='build_arch')]:
        if build_info['arch'] not in i:
            pytest.skip(f'tests required arch in {i!r}')
