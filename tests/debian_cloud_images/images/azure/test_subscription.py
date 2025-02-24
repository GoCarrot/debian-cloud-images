# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
import unittest.mock

from debian_cloud_images.images.azure.subscription import ImagesAzureSubscription


class TestImagesAzureSubscription:
    @pytest.fixture
    def azure_conn(self) -> unittest.mock.NonCallableMock:
        ret = unittest.mock.NonCallableMock()
        ret.request = unittest.mock.Mock(side_effect=self.mock_request)
        return ret

    def mock_request(self, path, *, method, **kw) -> unittest.mock.NonCallableMock:
        ret = unittest.mock.NonCallableMock()

        if method == 'GET':
            ret.parse_body = unittest.mock.Mock(return_value={
                'id': None,
            })
        else:
            raise RuntimeError(path, method, kw)

        return ret

    def test_get(self, azure_conn):
        r = ImagesAzureSubscription(
            'subscription',
            azure_conn,
        )

        assert r.data == {}

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='GET', data=None, params={'api-version': r.api_version}),
        ])
