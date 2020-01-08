import pytest

from debian_cloud_images.cli.upload_azure_cloudpartner import UploadAzureCloudpartnerCommand


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
        from debian_cloud_images.cli import upload_azure_cloudpartner
        ret = MagicMock()
        monkeypatch.setattr(upload_azure_cloudpartner, 'ImageUploaderAzureCloudpartner', ret)
        return ret

    def test___init__(self, config_file, mock_uploader):
        UploadAzureCloudpartnerCommand(
            config={
                'azure-auth': 'auth',
                'azure.cloudpartner.publisher': 'publisher',
                'azure-storage': 'storage',
            },
            config_file=config_file,
            output='output',
        )

        mock_uploader.assert_called_once_with(
            auth='auth',
            output='output',
            publish=None,
            publisher_id='publisher',
            storage_id='storage',
        )
