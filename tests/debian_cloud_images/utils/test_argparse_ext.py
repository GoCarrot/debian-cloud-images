import argparse
import os

from debian_cloud_images.utils.argparse_ext import ActionCommaSeparated, ActionEnv


def test_ActionCommaSeparated():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--comma',
        action=ActionCommaSeparated,
    )
    args = parser.parse_args(['--comma', ''])
    assert args.comma == []
    args = parser.parse_args(['--comma', ','])
    assert args.comma == []
    args = parser.parse_args(['--comma', 'a'])
    assert args.comma == ['a']
    args = parser.parse_args(['--comma', 'b'])
    assert args.comma == ['b']


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
