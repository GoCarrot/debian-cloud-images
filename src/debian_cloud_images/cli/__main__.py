import argparse

from .base import BaseCommand
from .build import BuildCommand
from .delete_azure_cloudpartner import DeleteAzureCloudpartnerCommand
from .release_azure_cloudpartner import ReleaseAzureCloudpartnerCommand
from .upload import UploadCommand
from .upload_azure import UploadAzureCommand
from .upload_azure_cloudpartner import UploadAzureCloudpartnerCommand
from .upload_ec2 import UploadEc2Command
from .upload_gce import UploadGceCommand


def main():
    early_parser = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    BaseCommand._argparse_register_config(early_parser)
    early_args, remainder_argv = early_parser.parse_known_args()

    config = BaseCommand._config_read(early_args.config_file)
    parser = argparse.ArgumentParser(
        prog='debian-cloud-images',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(help='sub-command help')

    BuildCommand._argparse_init_sub(subparsers, config)
    DeleteAzureCloudpartnerCommand._argparse_init_sub(subparsers, config)
    ReleaseAzureCloudpartnerCommand._argparse_init_sub(subparsers, config)
    UploadCommand._argparse_init_sub(subparsers, config)
    UploadAzureCommand._argparse_init_sub(subparsers, config)
    UploadAzureCloudpartnerCommand._argparse_init_sub(subparsers, config)
    UploadEc2Command._argparse_init_sub(subparsers, config)
    UploadGceCommand._argparse_init_sub(subparsers, config)

    args = parser.parse_args(remainder_argv)
    args.cls(**vars(args))()


if __name__ == '__main__':
    main()
