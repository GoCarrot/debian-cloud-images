import pytest

from debian_cloud_images.cli.upload_azure import (
    UploadAzureCommand,
    AzureAuth,
    AzureImage,
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
        from debian_cloud_images.cli import upload_azure
        ret = MagicMock()
        monkeypatch.setattr(upload_azure, 'ImageUploaderAzure', ret)
        return ret

    def test___init__(self, config_files, mock_uploader):
        UploadAzureCommand(
            config={
                'azure': {
                    'auth': {
                        'client': '00000000-0000-0000-0000-000000000001',
                        'secret': 'secret',
                    },
                    'image': {
                        'group': 'image-group',
                        'subscription': '00000000-0000-0000-0000-000000000002',
                        'tenant': '00000000-0000-0000-0000-000000000003',
                    },
                    'storage': {
                        'group': 'storage-group',
                        'name': 'name',
                        'subscription': '00000000-0000-0000-0000-000000000004',
                        'tenant': '00000000-0000-0000-0000-000000000005',
                    },
                },
            },
            config_files=config_files,
            generation=1,
            output='output',
        )

        mock_uploader.assert_called_once_with(
            auth=AzureAuth(
                client='00000000-0000-0000-0000-000000000001',
                secret='secret',
            ),
            generation=1,
            image=AzureImage(
                tenant='00000000-0000-0000-0000-000000000003',
                subscription='00000000-0000-0000-0000-000000000002',
                group='image-group',
            ),
            output='output',
            storage=AzureStorage(
                tenant='00000000-0000-0000-0000-000000000005',
                subscription='00000000-0000-0000-0000-000000000004',
                group='storage-group',
                name='name',
            ),
        )

    def test___init___noimage(self, config_files, mock_uploader):
        UploadAzureCommand(
            config={
                'azure': {
                    'auth': {
                        'client': '00000000-0000-0000-0000-000000000001',
                        'secret': 'secret',
                    },
                    'storage': {
                        'group': 'storage-group',
                        'name': 'name',
                        'subscription': '00000000-0000-0000-0000-000000000002',
                        'tenant': '00000000-0000-0000-0000-000000000003',
                    },
                },
            },
            config_files=config_files,
            generation=1,
            output='output',
        )

        mock_uploader.assert_called_once_with(
            auth=AzureAuth(
                client='00000000-0000-0000-0000-000000000001',
                secret='secret',
            ),
            generation=1,
            image=AzureImage(
                tenant='00000000-0000-0000-0000-000000000003',
                subscription='00000000-0000-0000-0000-000000000002',
                group='storage-group',
            ),
            output='output',
            storage=AzureStorage(
                tenant='00000000-0000-0000-0000-000000000003',
                subscription='00000000-0000-0000-0000-000000000002',
                group='storage-group',
                name='name',
            ),
        )
