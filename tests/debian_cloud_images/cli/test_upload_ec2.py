from debian_cloud_images.cli.upload_ec2 import UploadEc2Command


def test_args():
    UploadEc2Command._argparse_init_base()


def test():
    UploadEc2Command()
