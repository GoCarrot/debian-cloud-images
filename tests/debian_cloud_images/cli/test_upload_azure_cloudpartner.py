import pytest

from debian_cloud_images.cli.upload_azure_cloudpartner import (
    UploadAzureCloudpartnerCommand,
    AzureAuth,
    AzureCloudpartner,
    AzureStorage,
)


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
        from debian_cloud_images.cli import upload_azure_cloudpartner
        ret = MagicMock()
        monkeypatch.setattr(upload_azure_cloudpartner, 'ImageUploaderAzureCloudpartner', ret)
        return ret

    def test___init__(self, config_files, mock_uploader):
        UploadAzureCloudpartnerCommand(
            config={
                'azure': {
                    'auth': {
                        'client': '00000000-0000-0000-0000-000000000001',
                        'secret': 'secret',
                    },
                    'cloudpartner': {
                        'publisher': 'publisher',
                        'tenant': '00000000-0000-0000-0000-000000000002',
                    },
                    'storage': {
                        'group': 'storage-group',
                        'name': 'name',
                        'subscription': '00000000-0000-0000-0000-000000000003',
                        'tenant': '00000000-0000-0000-0000-000000000004',
                    },
                },
            },
            config_files=config_files,
            output='output',
        )

        mock_uploader.assert_called_once_with(
            auth=AzureAuth(
                client='00000000-0000-0000-0000-000000000001',
                secret='secret',
            ),
            cloudpartner=AzureCloudpartner(
                tenant='00000000-0000-0000-0000-000000000002',
                publisher='publisher',
            ),
            output='output',
            publish=None,
            storage=AzureStorage(
                tenant='00000000-0000-0000-0000-000000000004',
                subscription='00000000-0000-0000-0000-000000000003',
                group='storage-group',
                name='name',
            ),
        )
