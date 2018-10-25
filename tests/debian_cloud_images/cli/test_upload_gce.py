from debian_cloud_images.cli.upload_gce import UploadGceCommand


def test_args():
    UploadGceCommand._argparse_init_base()


def test():
    UploadGceCommand()
