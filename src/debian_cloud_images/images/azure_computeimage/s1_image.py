import logging
import time
import typing

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

logger = logging.getLogger(__name__)


class ImagesAzureComputeimageImage:
    __name_resource_group: str
    __name_image: str
    __conn: AzureGenericOAuth2Connection

    api_version: str = '2021-11-01'

    def __init__(
            self,
            resource_group: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
            *,
            properties: typing.Any = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_image = name
        self.__conn = conn

    @property
    def name(self) -> str:
        return self.__name_image

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.__conn.subscription_id}/resourceGroups/{self.__name_resource_group}/providers/Microsoft.Compute/images/{self.__name_image}'

    def __request(self, method: str, data: typing.Any = None) -> typing.Any:
        return self.__conn.request(self.path, method=method, data=data, params={'api-version': self.api_version})

    def create(
            self,
            location: str,
            properties: typing.Any,
            *,
            wait: bool = False,
    ) -> typing.Any:
        data = {
            'location': location,
            'properties': properties,
        }
        response = self.__request(method='PUT', data=data)
        data = response.parse_body()
        if wait:
            return self.wait_create()
        return data['properties']

    def get(self) -> typing.Any:
        response = self.__request(method='GET')
        data = response.parse_body()
        return data['properties']

    def wait_create(self, timeout=1800, interval=1):
        start_time = time.time()

        while time.time() - start_time < timeout:
            properties = self.get()
            state = properties['provisioningState'].lower()
            logging.debug('Privisioning state of image: %s', state)

            if state == 'succeeded':
                return properties
            elif state in ('creating', 'updating'):
                time.sleep(interval)
                continue
            else:
                raise RuntimeError('Image creation ended with unknown state: %s' % state)

        raise RuntimeError('Timeout while waiting for image creation to succeed')
