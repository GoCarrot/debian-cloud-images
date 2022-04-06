import collections.abc
import logging
import time
import typing

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

logger = logging.getLogger(__name__)


class ImagesAzureComputegalleryVersion:
    __name_resource_group: str
    __name_gallery: str
    __name_item: str
    __name_version: str
    __conn: AzureGenericOAuth2Connection

    api_version: str = '2021-10-01'

    def __init__(
            self,
            resource_group: str,
            gallery: str,
            item: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
            *,
            properties: typing.Any = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_gallery = gallery
        self.__name_item = item
        self.__name_version = name
        self.__conn = conn

    @property
    def name(self) -> str:
        return self.__name_version

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.__conn.subscription_id}/resourceGroups/{self.__name_resource_group}/providers/Microsoft.Compute/galleries/{self.__name_gallery}/images/{self.__name_item}/versions/{self.__name_version}'

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


class ImagesAzureComputegalleryVersions(collections.abc.Mapping):
    __items: typing.Mapping[str, ImagesAzureComputegalleryVersion]

    __name_resource_group: str
    __name_gallery: str
    __name_item: str
    __conn: AzureGenericOAuth2Connection

    api_version: str = '2021-10-01'

    def __init__(
            self,
            resource_group: str,
            gallery: str,
            item: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_gallery = gallery
        self.__name_item = item
        self.__conn = conn

        self.__items = {
            i['name']:
            ImagesAzureComputegalleryVersion(
                resource_group,
                gallery,
                item,
                i['name'],
                conn,
                properties=i['properties'],
            )
            for i in self.api_get()
        }

    def __getitem__(self, name: str) -> ImagesAzureComputegalleryVersion:
        return self.__items[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.__items)

    def __len__(self) -> int:
        return len(self.__items)

    @property
    def path(self) -> str:
        return f'/subscriptions/{self.__conn.subscription_id}/resourceGroups/{self.__name_resource_group}/providers/Microsoft.Compute/galleries/{self.__name_gallery}/images/{self.__name_item}/versions'

    def api_get(self) -> typing.Iterator[typing.Any]:
        response = self.__conn.request(self.path, method='GET', params={'api-version': self.api_version})
        body = response.parse_body()
        if 'nextLink' in body:
            raise NotImplementedError
        yield from body['value']
