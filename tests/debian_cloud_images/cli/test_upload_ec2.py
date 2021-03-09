import pytest

from debian_cloud_images.cli.upload_ec2 import UploadEc2Command


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
