import http
import logging
import typing

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzurePartnerlegacyOffer:
    __name_publisher: str
    __name_offer: str
    __conn: AzureGenericOAuth2Connection

    api_version = '2017-10-31'

    def __init__(
            self,
            publisher: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_publisher = publisher
        self.__name_offer = name
        self.__conn = conn

    @property
    def path(self) -> str:
        return f'/api/publishers/{self.__name_publisher}/offers/{self.__name_offer}'

    def __request(self, path: str, method: str, data: typing.Any = None) -> typing.Any:
        return self.__conn.request(path, method=method, data=data, params={'api-version': self.api_version})

    def get(self) -> typing.Any:
        response = self.__request(path=self.path, method='GET')
        return response.parse_body()

    def put(self, data: typing.Any) -> None:
        response = self.__request(path=self.path, method='PUT', data=data)
        if response.status != http.HTTPStatus.OK:
            raise RuntimeError('Failed')

    def control_golive(self) -> None:
        path = f'{self.path}/golive'
        self.__request(path=path, method='POST')

    def control_publish(self) -> None:
        path = f'{self.path}/publish'
        # E-mail address is actually ignored
        self.__request(path=path, method='POST', data={'metadata': {'notification-emails': 'jondoe@contoso.com'}})
