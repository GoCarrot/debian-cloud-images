import argparse
import os

from debian_cloud_images.utils.argparse_ext import ActionEnv, ConfigHashAction


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


def test_ConfigHashAction():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test',
        action=ConfigHashAction,
        config={'test': 'default1=value1 default2=value2'},
        config_key='test',
        nargs='+',
    )
    args = parser.parse_args(['--test', 'key1=value1'])
    assert args.test == {'key1': 'value1'}
    args = parser.parse_args(['--test', 'key1=value1', 'key2=value2'])
    assert args.test == {'key1': 'value1', 'key2': 'value2'}
    args = parser.parse_args(['--test', 'key1=value1', '--test', 'key2=value2'])
    assert args.test == {'key1': 'value1', 'key2': 'value2'}
    args = parser.parse_args([])
    assert args.test == {'default1': 'value1', 'default2': 'value2'}
