# SPDX-License-Identifier: GPL-2.0-or-later

import http
import pytest
import unittest.mock

from debian_cloud_images.images.azure.computedisk import (
    ImagesAzureComputedisk,
    ImagesAzureComputediskArch,
    ImagesAzureComputediskGeneration,
)
from debian_cloud_images.images.azure.resourcegroup import ImagesAzureResourcegroup


class TestImagesAzureComputedisk:
    @pytest.fixture
    def azure_conn(self) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()
        ret.request = unittest.mock.Mock(side_effect=self.mock_request)
        return ret

    def mock_request(self, path, *, method, **kw) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()

        if path == '/providers/Microsoft.Compute/disks/disk' and method == 'GET':
            ret.parse_body = unittest.mock.Mock(return_value={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'diskState': 'ReadyToUpload',
                    'provisioningState': 'Succeeded',
                },
            })
        elif path == '/providers/Microsoft.Compute/disks/disk' and method == 'PUT':
            ret.parse_body = unittest.mock.Mock(return_value={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Creating',
                },
            })
        elif path == '/providers/Microsoft.Compute/disks/disk/beginGetAccess' and method == 'POST':
            ret.status = http.HTTPStatus.ACCEPTED
            ret.headers = {
                'location': '/monitor/beginGetAccess',
            }
        elif path == '/providers/Microsoft.Compute/disks/disk/endGetAccess' and method == 'POST':
            ret.status = http.HTTPStatus.ACCEPTED
            ret.headers = {
                'location': '/monitor/endGetAccess',
            }
        elif path == '/monitor/beginGetAccess?' and method == 'GET':
            ret.status = http.HTTPStatus.OK
            ret.parse_body = unittest.mock.Mock(return_value={
                'accessSAS': 'https://storage/',
            })
        elif path == '/monitor/endGetAccess?' and method == 'GET':
            ret.status = http.HTTPStatus.OK
        else:
            raise RuntimeError(path, method, kw)

        return ret

    @pytest.fixture
    def storage_conn_cls(self) -> unittest.mock.Mock:
        conn = unittest.mock.NonCallableMock()
        conn.request = unittest.mock.Mock(side_effect=self.mock_storage)
        ret = unittest.mock.Mock(return_value=conn)
        return ret

    def mock_storage(self, path, *, method, **kw) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()

        if method == 'PUT':
            ret.status = http.HTTPStatus.CREATED
        else:
            raise RuntimeError(path, method, kw)

        return ret

    def test_get(self, azure_conn):
        resourcegroup = unittest.mock.NonCallableMock(spec=ImagesAzureResourcegroup)
        resourcegroup.path = ''

        r = ImagesAzureComputedisk(
            resourcegroup,
            'disk',
            conn=azure_conn,
        )

        assert r.path == '/providers/Microsoft.Compute/disks/disk'
        assert r.properties == {
            'diskState': 'ReadyToUpload',
            'provisioningState': 'Succeeded',
        }

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='GET', data=unittest.mock.ANY, params={'api-version': r.api_version}),
        ])

    def test_create(self, azure_conn):
        resourcegroup = unittest.mock.NonCallableMock(spec=ImagesAzureResourcegroup)
        resourcegroup.path = ''

        r = ImagesAzureComputedisk.create(
            resourcegroup,
            'disk',
            conn=azure_conn,
            arch=ImagesAzureComputediskArch.amd64,
            generation=ImagesAzureComputediskGeneration.v2,
            location='location',
            size=10,
        )

        assert r.properties == {
            'diskState': 'ReadyToUpload',
            'provisioningState': 'Succeeded',
        }

        azure_conn.assert_has_calls([
            unittest.mock.call.request(r.path, method='PUT', data=unittest.mock.ANY, params={'api-version': r.api_version}),
        ])

    def test_upload(self, azure_conn, storage_conn_cls, mocker):
        # Compute disk support uses plain Connection right now
        mocker.patch('debian_cloud_images.images.azure.computedisk.Connection', storage_conn_cls)

        resourcegroup = unittest.mock.NonCallableMock(spec=ImagesAzureResourcegroup)
        resourcegroup.path = ''

        r = ImagesAzureComputedisk(
            resourcegroup,
            'disk',
            azure_conn,
        )

        with open(__file__, 'rb') as f:
            r.upload(f)

        azure_conn.assert_has_calls([
            unittest.mock.call.request(f'{r.path}/beginGetAccess', method='POST', data=unittest.mock.ANY, params={'api-version': r.api_version}),
            unittest.mock.call.request('/monitor/beginGetAccess?', method='GET'),
            unittest.mock.call.request(f'{r.path}/endGetAccess', method='POST', data={}, params={'api-version': r.api_version}),
            unittest.mock.call.request('/monitor/endGetAccess?', method='GET'),
        ])
