# SPDX-License-Identifier: GPL-2.0-or-later

import httpx
import pytest
import unittest.mock

from debian_cloud_images.backend.azure import (
    AzureVmArch,
    AzureVmGeneration,
)
from debian_cloud_images.backend.azure.computedisk import AzureComputedisk
from debian_cloud_images.backend.azure.resourcegroup import AzureResourcegroup


class TestAzureComputedisk:
    @pytest.fixture
    def client(self) -> unittest.mock.Mock:
        ret = unittest.mock.NonCallableMock()
        ret.request = unittest.mock.Mock(side_effect=self.mock_request)
        return ret

    def mock_request(self, *, url, method, **kw) -> unittest.mock.Mock:
        ret = unittest.mock.Mock()
        ret.headers = {
            'content-type': 'application/json',
        }

        if url == 'https://management.azure.com/BASE/providers/Microsoft.Compute/disks/disk' and method == 'GET':
            ret.json = unittest.mock.Mock(return_value={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'diskState': 'ReadyToUpload',
                    'provisioningState': 'Succeeded',
                },
            })
        elif url == 'https://management.azure.com/BASE/providers/Microsoft.Compute/disks/disk' and method == 'PUT':
            ret.json = unittest.mock.Mock(return_value={
                'id': None,
                'name': None,
                'location': 'location',
                'properties': {
                    'provisioningState': 'Creating',
                },
            })
        elif url == 'https://management.azure.com/BASE/providers/Microsoft.Compute/disks/disk/beginGetAccess' and method == 'POST':
            ret.status_code = httpx.codes.ACCEPTED
            ret.headers = {
                'content-type': 'undefined',
                'location': '/monitor/beginGetAccess',
            }
        elif url == 'https://management.azure.com/BASE/providers/Microsoft.Compute/disks/disk/endGetAccess' and method == 'POST':
            ret.status_code = httpx.codes.ACCEPTED
            ret.headers = {
                'content-type': 'undefined',
                'location': '/monitor/endGetAccess',
            }
        elif url == '/monitor/beginGetAccess' and method == 'GET':
            ret.status_code = httpx.codes.OK
            ret.json = unittest.mock.Mock(return_value={
                'accessSAS': '/storage',
            })
        elif url == '/monitor/endGetAccess' and method == 'GET':
            ret.status_code = httpx.codes.OK
        elif url == '/storage' and method == 'PUT':
            ret.status_code = httpx.codes.CREATED
        else:
            raise RuntimeError(url, method, kw)

        return ret

    def test_get(self, client) -> None:
        resourcegroup = unittest.mock.NonCallableMock(spec=AzureResourcegroup)
        resourcegroup.client = client
        resourcegroup.path = 'BASE'

        r = AzureComputedisk(
            resourcegroup,
            'disk',
        )

        assert r.path == 'BASE/providers/Microsoft.Compute/disks/disk'
        assert r.data() == {
            'location': 'location',
            'properties': {
                'diskState': 'ReadyToUpload',
                'provisioningState': 'Succeeded',
            },
        }

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='GET', json=unittest.mock.ANY, params={'api-version': r.api_version}),
        ])

    def test_create(self, client) -> None:
        resourcegroup = unittest.mock.NonCallableMock(spec=AzureResourcegroup)
        resourcegroup.client = client
        resourcegroup.path = 'BASE'

        r = AzureComputedisk.create(
            resourcegroup,
            'disk',
            arch=AzureVmArch.amd64,
            generation=AzureVmGeneration.v2,
            location='location',
            size=10,
        )

        assert r.data() == {
            'location': 'location',
            'properties': {
                'diskState': 'ReadyToUpload',
                'provisioningState': 'Succeeded',
            },
        }

        client.assert_has_calls([
            unittest.mock.call.request(url=r.url(), method='PUT', json=unittest.mock.ANY, params={'api-version': r.api_version}),
        ])

    def test_upload(self, client) -> None:
        resourcegroup = unittest.mock.NonCallableMock(spec=AzureResourcegroup)
        resourcegroup.client = client
        resourcegroup.path = 'BASE'

        r = AzureComputedisk(
            resourcegroup,
            'disk',
        )

        with open(__file__, 'rb') as f:
            r.upload(f)

        client.assert_has_calls([
            unittest.mock.call.request(url=f'{r.url()}/beginGetAccess', method='POST', json=unittest.mock.ANY, params={'api-version': r.api_version}),
            unittest.mock.call.request(url='/monitor/beginGetAccess', method='GET'),
            unittest.mock.call.request(url='/storage', method='PUT', params={'comp': 'page'}, headers=unittest.mock.ANY, content=unittest.mock.ANY),
            unittest.mock.call.request(url=f'{r.url()}/endGetAccess', method='POST', json={}, params={'api-version': r.api_version}),
            unittest.mock.call.request(url='/monitor/endGetAccess', method='GET'),
        ])
