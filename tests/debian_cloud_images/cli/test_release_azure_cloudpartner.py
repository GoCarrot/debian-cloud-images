import pytest

from debian_cloud_images.cli.release_azure_cloudpartner import ReleaseAzureCloudpartnerCommand


class TestCommand:
    @pytest.fixture
    def config_file(self, tmp_path):
        p = tmp_path / 'config'
        with p.open(mode='w') as f:
            f.write('')
        return p.as_posix()

    def test___init__(self, config_file):
        c = ReleaseAzureCloudpartnerCommand(
            config={
                'azure-auth': 'auth',
                'azure.cloudpartner.publisher': 'publisher',
            },
            config_file=config_file,
        )

        assert c.auth == 'auth'
        assert c.publisher_id == 'publisher'
