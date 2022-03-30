import collections.abc
import logging
import typing

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

from .s2_version import ImagesAzureComputegalleryVersions

logger = logging.getLogger(__name__)


class ImagesAzureComputegalleryItem:
    __name_resource_group: str
    __name_gallery: str
    __name_item: str
    __conn: AzureGenericOAuth2Connection
    properties: typing.Any

    api_version: str = '2021-10-01'

    def __init__(
            self,
            resource_group: str,
            gallery: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
            *,
            data: typing.Any = None,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_gallery = gallery
        self.__name_item = name
        self.__conn = conn

        if data is None:
            data = self.api_get()
        self.properties = data['properties']

    @property
    def name(self) -> str:
        return self.__name_item

    @property
    def versions(self) -> ImagesAzureComputegalleryVersions:
        return ImagesAzureComputegalleryVersions(
            self.__name_resource_group,
            self.__name_gallery,
            self.__name_item,
            self.__conn,
        )

    @property
    def api_path(self) -> str:
        return f'/subscriptions/{self.__conn.subscription_id}/resourceGroups/{self.__name_resource_group}/providers/Microsoft.Compute/galleries/{self.__name_gallery}/images/{self.__name_item}'

    def api_get(self) -> typing.Any:
        response = self.__conn.request(self.api_path, method='GET', params={'api_version': self.api_version})
        return response.parse_body()


class ImagesAzureComputegalleryItems(collections.abc.Mapping):
    __items: typing.Mapping[str, ImagesAzureComputegalleryItem]

    __name_resource_group: str
    __name_gallery: str
    __conn: AzureGenericOAuth2Connection

    api_version: str = '2021-10-01'

    def __init__(
            self,
            resource_group: str,
            gallery: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_gallery = gallery
        self.__conn = conn

        self.__items = {
            i['name']:
            ImagesAzureComputegalleryItem(
                resource_group,
                gallery,
                i['name'],
                conn,
                data=i,
            )
            for i in self.api_get()
        }

    def __getitem__(self, name: str) -> ImagesAzureComputegalleryItem:
        return self.__items[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.__items)

    def __len__(self) -> int:
        return len(self.__items)

    @property
    def api_path(self) -> str:
        return f'/subscriptions/{self.__conn.subscription_id}/resourceGroups/{self.__name_resource_group}/providers/Microsoft.Compute/galleries/{self.__name_gallery}/images'

    def api_get(self) -> typing.Iterator[typing.Any]:
        response = self.__conn.request(self.api_path, method='GET', params={'api_version': self.api_version})
        body = response.parse_body()
        if 'nextLink' in body:
            raise NotImplementedError
        yield from body['value']
