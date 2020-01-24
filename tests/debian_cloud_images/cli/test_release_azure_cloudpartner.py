import pytest

from debian_cloud_images.cli.release_azure_cloudpartner import (
    ReleaseAzureCloudpartnerCommand,
    AzureAuth,
    AzureCloudpartner,
)


class TestCommand:
    @pytest.fixture
    def config_files(self, tmp_path):
        p = tmp_path / 'config'
        with p.open(mode='w') as f:
            f.write('')
        return [p.as_posix()]

    def test___init__(self, config_files):
        c = ReleaseAzureCloudpartnerCommand(
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
