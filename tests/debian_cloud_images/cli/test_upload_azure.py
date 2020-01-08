import pytest

from debian_cloud_images.cli.upload_azure import UploadAzureCommand


class TestCommand:
    @pytest.fixture
    def config_file(self, tmp_path):
        p = tmp_path / 'config'
        with p.open(mode='w') as f:
            f.write('')
        return p.as_posix()

    @pytest.fixture
    def mock_uploader(self, monkeypatch):
        from unittest.mock import MagicMock
        from debian_cloud_images.cli import upload_azure
        ret = MagicMock()
        monkeypatch.setattr(upload_azure, 'ImageUploaderAzure', ret)
        return ret

    def test___init__(self, config_file, mock_uploader):
        UploadAzureCommand(
            config={
                'azure-auth': 'auth',
                'azure-group': 'group',
                'azure-storage': 'storage',
            },
            config_file=config_file,
            generation=1,
            output='output',
        )

        mock_uploader.assert_called_once_with(
            auth='auth',
            generation=1,
            image_group='group',
            output='output',
            storage_group='group',
            storage_id='storage',
        )
