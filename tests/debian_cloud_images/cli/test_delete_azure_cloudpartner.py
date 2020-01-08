import pytest

from debian_cloud_images.cli.delete_azure_cloudpartner import DeleteAzureCloudpartnerCommand


class TestCommand:
    @pytest.fixture
    def config_file(self, tmp_path):
        p = tmp_path / 'config'
        with p.open(mode='w') as f:
            f.write('')
        return p.as_posix()

    def test___init__(self, config_file):
        c = DeleteAzureCloudpartnerCommand(
            config={
                'azure-auth': 'auth',
                'azure.cloudpartner.publisher': 'publisher',
                'azure-storage': 'storage',
            },
            config_file=config_file,
        )

        assert c.auth == 'auth'
        assert c.publisher_id == 'publisher'
        assert c.storage_id == 'storage'
