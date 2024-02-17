# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.cli.upload_gce import UploadGceCommand


class TestCommand:
    @pytest.fixture
    def auth_file(self, tmp_path):
        p = tmp_path / 'auth.json'
        with p.open(mode='w') as f:
            f.write('{}')
        return p.as_posix()

    @pytest.fixture
    def config_files(self, tmp_path):
        p = tmp_path / 'config'
        with p.open(mode='w') as f:
            f.write('')
        return [p.as_posix()]

    @pytest.fixture
    def mock_env(self, monkeypatch):
        monkeypatch.delenv('GOOGLE_APPLICATION_CREDENTIALS', raising=False)
        return monkeypatch

    @pytest.fixture
    def mock_uploader(self, monkeypatch):
        from unittest.mock import MagicMock
        from debian_cloud_images.cli import upload_gce
        ret = MagicMock()
        monkeypatch.setattr(upload_gce, 'ImageUploaderGce', ret)
        return ret

    def test___init__(self, auth_file, config_files, mock_env, mock_uploader):
        UploadGceCommand(
            config={
                'gce.auth.credentialsfile': auth_file,
                'gce.image.project': 'project',
                'gce.storage.name': 'bucket',
            },
            config_files=config_files,
            output='output',
        )

        mock_uploader.assert_called_once_with(
            auth={},
            bucket='bucket',
            output='output',
            project='project',
        )
