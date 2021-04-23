import pytest

from debian_cloud_images.cli.cleanup_azure_cloudpartner import (
    CleanupAzureCloudpartnerCommand,
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

    def test___init__(self, config_files):
        c = CleanupAzureCloudpartnerCommand(
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
        )

        assert c.auth == AzureAuth(
            client='00000000-0000-0000-0000-000000000001',
            secret='secret',
        )
        assert c.cloudpartner == AzureCloudpartner(
            tenant='00000000-0000-0000-0000-000000000002',
            publisher='publisher',
        )
        assert c.storage == AzureStorage(
            tenant='00000000-0000-0000-0000-000000000004',
            subscription='00000000-0000-0000-0000-000000000003',
            group='storage-group',
            name='name',
        )
