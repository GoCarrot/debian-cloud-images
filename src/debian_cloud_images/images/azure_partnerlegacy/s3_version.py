import logging
import typing

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzurePartnerlegacyVersion:
    __name_publisher: str
    __name_offer: str
    __name_plan: str
    __name_version: str
    __conn: AzureGenericOAuth2Connection

    api_version = '2017-10-31'

    def __init__(
            self,
            publisher: str,
            offer: str,
            plan: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_publisher = publisher
        self.__name_offer = offer
        self.__name_plan = plan
        self.__name_version = name
        self.__conn = conn

    @property
    def name(self) -> str:
        return self.__name_version

    def __request(self, method: str, data: typing.Any = None) -> typing.Any:
        path = f'/api/publishers/{self.__name_publisher}/offers/{self.__name_offer}'
        return self.__conn.request(path, method=method, data=data, params={'api-version': self.api_version})

    def __get_plan(self) -> typing.Any:
        " Request complete offer, find and return plan "
        response = self.__request(method='GET')
        data = response.parse_body()
        plans = list(filter(lambda i: i['planId'] == self.__name_plan, data['definition']['plans']))
        if len(plans) != 1:
            raise RuntimeError('Plan not found')
        return response, data, plans[0]

    def create(
            self,
            description: str,
            legacy_name: str,
            legacy_label: str,
            url: str,
    ) -> typing.Any:
        response, data, plan = self.__get_plan()
        versions = plan['microsoft-azure-corevm.vmImagesPublicAzure']
        ret = versions[self.__name_version] = {
            'description': description,
            'label': legacy_label,
            'mediaName': legacy_name,
            'osVhdUrl': url,
        }
        for generation in plan['diskGenerations']:
            versions = generation['microsoft-azure-corevm.vmImagesPublicAzure']
            # Legacy images names needs to be unique
            suffix = generation['planId'].rsplit('-', 1)[-1]
            versions[self.__name_version] = {
                'description': description,
                'label': f'{legacy_label}-{suffix}',
                'mediaName': f'{legacy_name}-{suffix}',
                'osVhdUrl': url,
            }
        self.__request(method='PUT', data=data)
        return ret

    def get(self) -> typing.Any:
        response, data, plan = self.__get_plan()
        versions = plan['microsoft-azure-corevm.vmImagesPublicAzure']
        return versions[self.__name_version]
