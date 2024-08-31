# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.cli.upload_ec2 import UploadEc2Command
from libcloud.common.exceptions import BaseHTTPError


class TestCommand:
    @pytest.fixture
    def config_files(self, tmp_path):
        p = tmp_path / 'config'
        with p.open(mode='w') as f:
            f.write('')
        return [p.as_posix()]

    @pytest.fixture
    def mock_uploader(self, monkeypatch):
        from unittest.mock import MagicMock
        from debian_cloud_images.cli import upload_ec2
        ret = MagicMock()
        monkeypatch.setattr(upload_ec2, 'ImageUploaderEc2', ret)
        return ret

    @pytest.fixture
    def raise_basehttperror(self):
        def _raise_basehttperror(*args):
            raise BaseHTTPError(code=418, message="ResourceLimitExceeded: testing")
        return _raise_basehttperror

    def test___init__(self, config_files, mock_uploader):
        c = UploadEc2Command(
            config={
                'ec2': {
                    'auth': {
                        'key': 'access_key_id',
                        'secret': 'access_secret_key',
                        'token': 'access_session_token',
                    },
                    'storage': {
                        'name': 'bucket',
                    },
                    'image': {
                        'regions': ['all'],
                        'tags': ['Tag=Value'],
                    },
                },
            },
            config_files=config_files,
            output='output',
            permission_public='permission_public',
        )
        print(c.config)

        mock_uploader.assert_called_once_with(
            add_tags={'Tag': 'Value'},
            bucket='bucket',
            key='access_key_id',
            output='output',
            permission_public='permission_public',
            regions=['all'],
            secret='access_secret_key',
            token='access_session_token',
        )

    def test_create_image(self, monkeypatch, raise_basehttperror):
        from debian_cloud_images.cli import upload_ec2
        from unittest.mock import MagicMock
        pi = MagicMock()
        image = MagicMock()
        monkeypatch.setattr(image, 'build_arch', 'arm64')
        snapshot = MagicMock()
        monkeypatch.setattr(snapshot, 'id', "snap-012345689")
        test_driver = MagicMock()
        monkeypatch.setattr(snapshot, 'driver', test_driver)
        monkeypatch.setattr(pi, 'vendor_name', "debian-tests")
        monkeypatch.setattr(pi, 'vendor_description', "debian tests vendor description")
        uploader = upload_ec2.ImageUploaderEc2(
            output=None,
            bucket=None,
            key="dummy-key",
            secret="dummy-secret",
            token="dummy-token",
            regions=["us-west-2"],
            add_tags=None,
            permission_public=True)

        # This should get a gp2 volume
        monkeypatch.setattr(image, 'build_release_id', '10')

        uploader.create_image(image, pi, [snapshot])
        test_driver.ex_register_image.assert_called_once_with(
            name='debian-tests',
            description="debian tests vendor description",
            architecture='arm64',
            block_device_mapping=[{'DeviceName': '/dev/xvda',
                                   'Ebs': {'SnapshotId': "snap-012345689",
                                           'VolumeType': 'gp2',
                                           'DeleteOnTermination': 'true',
                                           }}],
            root_device_name='/dev/xvda',
            virtualization_type='hvm',
            ena_support=True,
            sriov_net_support='simple')

        test_driver.ex_create_tags.assert_called_once()
        test_driver.ex_modify_image_attribute.assert_called_once()

        # This should get a gp3 volume with additional performance settings
        monkeypatch.setattr(image, 'build_release_id', '12')
        test_driver.reset_mock()

        uploader.create_image(image, pi, [snapshot])
        test_driver.ex_register_image.assert_called_once_with(
            name='debian-tests',
            description="debian tests vendor description",
            architecture='arm64',
            block_device_mapping=[{'DeviceName': '/dev/xvda',
                                   'Ebs': {'SnapshotId': "snap-012345689",
                                           'VolumeType': 'gp3',
                                           'DeleteOnTermination': 'true',
                                           'Iops': 3000,
                                           'Throughput': 125}}],
            root_device_name='/dev/xvda',
            virtualization_type='hvm',
            ena_support=True,
            sriov_net_support='simple')

        test_driver.ex_create_tags.assert_called_once()
        test_driver.ex_modify_image_attribute.assert_called_once()

        test_driver.reset_mock()
        monkeypatch.setenv("NO_RETRY_DELAY", "true")
        monkeypatch.setattr(test_driver, 'ex_modify_image_attribute', raise_basehttperror)

        uploader.create_image(image, pi, [snapshot])
        test_driver.ex_register_image.assert_called_once_with(
            name='debian-tests',
            description="debian tests vendor description",
            architecture='arm64',
            block_device_mapping=[{'DeviceName': '/dev/xvda',
                                   'Ebs': {'SnapshotId': "snap-012345689",
                                           'VolumeType': 'gp3',
                                           'DeleteOnTermination': 'true',
                                           'Iops': 3000,
                                           'Throughput': 125}}],
            root_device_name='/dev/xvda',
            virtualization_type='hvm',
            ena_support=True,
            sriov_net_support='simple')

        test_driver.ex_create_tags.assert_called_once()
        assert uploader._api_error_count == 1
