# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import os

from debian_cloud_images.utils.argparse_ext import ActionEnv


def test_ActionEnv():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--home',
        action=ActionEnv,
        env='HOME',
        help='use home',
    )
    args = parser.parse_args(['--home', 'test'])
    assert args.home == 'test'
    args = parser.parse_args([])
    assert args.home == os.environ['HOME']
