#!/usr/bin/env python3

import datetime
import logging
import pytest

from debian_cloud_images.images.ec2.s2_cloud_version import StepCloudVersions, StepCloudVersion
from debian_cloud_images.images.ec2.info import Ec2Info
from debian_cloud_images.images.publicinfo import ImagePublicInfo
from debian_cloud_images.utils.libcloud.compute.ec2 import ExEC2NodeDriver, ExEC2Region
from debian_cloud_images.utils.libcloud.storage.s3 import S3BucketStorageDriver
from debian_cloud_images.utils.image_version import ImageVersion
from debian_cloud_images.cli.cleanup_ec2 import CleanupEc2Command
from libcloud.compute.base import NodeImage, VolumeSnapshot
from libcloud.common.exceptions import BaseHTTPError, exception_from_message


class FakeS3BucketStorageDriver(S3BucketStorageDriver):
    def __init__(self, bucket, key):
        self.region_name = "us-fake-1"
        logging.debug("Initializing FakeS3BucketStorageDriver")


@pytest.fixture
def mock_ec2info():
    drivers_compute = ExEC2NodeDriver("us-fake-1")
    storage_driver = FakeS3BucketStorageDriver(bucket="dummy-bucket",
                                               key="/images",)
    image_public_info = ImagePublicInfo()
    return Ec2Info(noop=False,
                   public=image_public_info,
                   account="dummy-aws",
                   drivers_compute=drivers_compute,
                   driver_storage=storage_driver,
                   )


@pytest.fixture
def mock_ec2_config():
    return {
        'ec2.auth.key': 'fake-key',
        'ec2.auth.secret': 'fake-secret',
        'ec2.auth.token': 'fake-token',
        'ec2.image.regions': 'all',
    }


class TestCleanup:

    def mockregions(n):
        return [
            ExEC2Region('us-fake-1', 'https://localhost/'),
        ]

    def mocklistsnapshots(*args, **kwargs):
        return [
            VolumeSnapshot('snap-asdf',
                           ExEC2NodeDriver,
                           created=datetime.datetime(2024, 8, 23, tzinfo=datetime.timezone.utc),
                           extra={
                               'tags': {
                                   'ImageFamily': 'dev',
                                   'ImageVersion': '20240823-1848',
                               },
                           },
                           ),
            VolumeSnapshot('snap-quux',
                           ExEC2NodeDriver,
                           created=datetime.datetime(2024, 7, 1, tzinfo=datetime.timezone.utc),
                           extra={
                               'tags': {
                                   'ImageFamily': 'dev',
                                   'ImageVersion': '20240701-1001',
                                   'AMI': 'ami-dummy0002',
                               },
                           },
                           ),
        ]

    def mocklistimages(*args, **kwargs):
        return [
            NodeImage(id='ami-dummy0001',
                      name='my-first-ami',
                      driver=ExEC2NodeDriver,
                      extra={
                          'tags': {
                              'my-tag': 'my-value',
                              'ImageFamily': 'dev',
                              'ImageVersion': '20240823-1848',
                          },
                          'block_device_mapping': {},
                      },
                      ),
            NodeImage(id='ami-dummy0002',
                      name='my-second-ami',
                      driver=ExEC2NodeDriver,
                      extra={
                          'tags': {
                              'ImageFamily': 'dev',
                              'ImageVersion': '20240701-1001',
                          },
                          'block_device_mapping': {},
                      },
                      ),
        ]

    def mockdelete_image(*args):
        return

    def mockdelete_snapshot(*args):
        return

    def test_cleanup_cloud_versions(self, monkeypatch, mock_ec2info, mock_ec2_config, caplog):
        v = StepCloudVersions(mock_ec2info)
        v._children["20240823-1848"] = StepCloudVersion(v, ImageVersion.from_string("20240823-1848"))
        v._children["20240701-1001"] = StepCloudVersion(v, ImageVersion.from_string("20240701-1001"))
        monkeypatch.setattr(ExEC2NodeDriver, "ex_list_regions", TestCleanup.mockregions)
        monkeypatch.setattr(ExEC2NodeDriver, "list_images", TestCleanup.mocklistimages)
        monkeypatch.setattr(ExEC2NodeDriver, "list_snapshots", TestCleanup.mocklistsnapshots)
        monkeypatch.setattr(ExEC2NodeDriver, "delete_image", TestCleanup.mockdelete_image)
        monkeypatch.setattr(ExEC2NodeDriver, "destroy_volume_snapshot", TestCleanup.mockdelete_snapshot)
        caplog.set_level(logging.DEBUG)

        CleanupEc2Command(config=mock_ec2_config,
                          delete_after=30,
                          date_today=datetime.datetime(2024, 8, 28,
                                                       hour=1, minute=10, second=49, microsecond=0,),
                          )()

    def test_cleanup_cloud_versions_missing_snapshot(self, monkeypatch, mock_ec2info, mock_ec2_config, caplog):
        def raise_exception(*args):
            raise exception_from_message(code=418,
                                         message="InvalidSnapshot.NotFound: (ec2 error text goes here).",
                                         headers={})

        v = StepCloudVersions(mock_ec2info)
        v._children["20240823-1848"] = StepCloudVersion(v, ImageVersion.from_string("20240823-1848"))
        v._children["20240701-1001"] = StepCloudVersion(v, ImageVersion.from_string("20240701-1001"))
        monkeypatch.setattr(ExEC2NodeDriver, "ex_list_regions", TestCleanup.mockregions)
        monkeypatch.setattr(ExEC2NodeDriver, "list_images", TestCleanup.mocklistimages)
        monkeypatch.setattr(ExEC2NodeDriver, "list_snapshots", TestCleanup.mocklistsnapshots)
        monkeypatch.setattr(ExEC2NodeDriver, "delete_image", TestCleanup.mockdelete_image)
        monkeypatch.setattr(ExEC2NodeDriver, "destroy_volume_snapshot", raise_exception)
        caplog.set_level(logging.DEBUG)

        CleanupEc2Command(config=mock_ec2_config,
                          delete_after=30,
                          date_today=datetime.datetime(2024, 8, 28,
                                                       hour=1, minute=10, second=49, microsecond=0,),
                          )()

    def test_cleanup_cloud_versions_internal_error(self, monkeypatch, mock_ec2info, mock_ec2_config, caplog):
        def raise_exception(*args):
            raise exception_from_message(code=500,
                                         message="InternalError: An internal error has occurred",
                                         headers={})

        v = StepCloudVersions(mock_ec2info)
        v._children["20240823-1848"] = StepCloudVersion(v, ImageVersion.from_string("20240823-1848"))
        v._children["20240701-1001"] = StepCloudVersion(v, ImageVersion.from_string("20240701-1001"))
        monkeypatch.setattr(ExEC2NodeDriver, "ex_list_regions", TestCleanup.mockregions)
        monkeypatch.setattr(ExEC2NodeDriver, "list_images", TestCleanup.mocklistimages)
        monkeypatch.setattr(ExEC2NodeDriver, "list_snapshots", TestCleanup.mocklistsnapshots)
        monkeypatch.setattr(ExEC2NodeDriver, "delete_image", TestCleanup.mockdelete_image)
        monkeypatch.setattr(ExEC2NodeDriver, "destroy_volume_snapshot", raise_exception)
        monkeypatch.setenv("NO_RETRY_DELAY", "true")
        caplog.set_level(logging.DEBUG)

        with pytest.raises(BaseHTTPError) as e:
            CleanupEc2Command(config=mock_ec2_config,
                              delete_after=30,
                              date_today=datetime.datetime(2024, 8, 28,
                                                           hour=1, minute=10, second=49, microsecond=0,),
                              )()
            assert "InternalError" in str(e.value)


# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
