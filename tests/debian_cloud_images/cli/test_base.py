from debian_cloud_images.cli.base import BaseCommand


def test_args():
    BaseCommand._argparse_init_base()


def test():
    BaseCommand()
