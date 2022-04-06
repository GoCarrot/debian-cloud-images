import argparse

from .build import BuildCommand
from .cleanup import CleanupCommand
from .cleanup_ec2 import CleanupEc2Command
from .upload import UploadCommand
from .upload_azure import UploadAzureCommand
from .upload_azure_computegallery import UploadAzureComputegalleryCommand
from .upload_azure_partner import UploadAzurePartnerlegacyCommand
from .upload_ec2 import UploadEc2Command
from .upload_gce import UploadGceCommand
from .put_ssm import PutSSMCommand


def main():
    parser = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
        prog='debian-cloud-images',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        help='sub-command help',
    )

    BuildCommand._argparse_init_sub(subparsers)
    CleanupCommand._argparse_init_sub(subparsers)
    CleanupEc2Command._argparse_init_sub(subparsers)
    UploadCommand._argparse_init_sub(subparsers)
    UploadAzureCommand._argparse_init_sub(subparsers)
    UploadAzureComputegalleryCommand._argparse_init_sub(subparsers)
    UploadAzurePartnerlegacyCommand._argparse_init_sub(subparsers)
    UploadEc2Command._argparse_init_sub(subparsers)
    UploadGceCommand._argparse_init_sub(subparsers)
    PutSSMCommand._argparse_init_sub(subparsers)

    args = parser.parse_args()
    args.cls(argparser=parser, **vars(args))()


if __name__ == '__main__':
    main()
