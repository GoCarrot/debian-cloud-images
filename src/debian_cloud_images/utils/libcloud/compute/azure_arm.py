# SPDX-License-Identifier: GPL-2.0-or-later

import time
import typing

from libcloud.compute.drivers.azure_arm import AzureNodeDriver

from ..common.azure import AzureGenericOAuth2Connection


class ExAzureNodeDriver(AzureNodeDriver):
    connectionCls: typing.Type = AzureGenericOAuth2Connection

    def __init__(self, *, client_id, client_secret, subscription_id, tenant_id):
        self.client_id = client_id
        self.client_secret = client_secret

        super().__init__(key='', secret='', tenant_id=tenant_id, subscription_id=subscription_id)

    def _ex_connection_class_kwargs(self):
        ret = super()._ex_connection_class_kwargs()
        ret.update({
            'host': 'management.azure.com',
            'login_resource': 'https://management.core.windows.net/',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'tenant_id': self.tenant_id,
        })
        return ret

    def ex_create_computeimage(self, name, ex_resource_group, location, ex_blob, ex_generation=1, wait_for_completion=True):
        action = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/images/{}'.format(
            self.subscription_id,
            ex_resource_group,
            name,
        )

        data = {
            'location': location,
            'properties': {
                'hyperVGeneration': f'V{ex_generation}',
                'storageProfile': {
                    'osDisk': {
                        'osType': 'Linux',
                        'blobUri': ex_blob,
                        'osState': 'Generalized',
                    }
                }
            }
        }

        self.connection.request(action, data=data, method='PUT', params={'api-version': '2019-03-01'})

        if wait_for_completion:
            self._wait_create_computeimage(action)

        return action

    def _wait_create_computeimage(self, action, timeout=180, interval=1):
        start_time = time.time()

        while time.time() - start_time < timeout:
            resp = self.connection.request(action, params={'api-version': '2018-06-01'}).object
            state = resp['properties']['provisioningState'].lower()

            if state == 'succeeded':
                return
            elif state == 'creating':
                time.sleep(interval)
                continue
            else:
                raise RuntimeError('Image creation ended with unknown state: %s' % state)

        raise RuntimeError('Timeout while waiting for image creation to succeed')
