# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import typing

from debian_cloud_images.api.cdo.image_config import ImageConfigArch
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from typing import Optional


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

    def __request(self, method: str, data: Optional[typing.Any] = None) -> typing.Any:
        path = f'/api/publishers/{self.__name_publisher}/offers/{self.__name_offer}'
        return self.__conn.request(path, method=method, data=data, params={'api-version': self.api_version})

    def __get_plan(self) -> typing.Any:
        " Request complete offer, find and return plan "
        response = self.__request(method='GET')
        data = response.parse_body()
        # Workaround, can't write these key
        offer = data['definition']['offer']
        offer.pop('microsoft-azure-corevm.legacyOfferId', None)
        offer.pop('microsoft-azure-corevm.legacyPublisherId', None)
        plans = list(filter(lambda i: i['planId'] == self.__name_plan, data['definition']['plans']))
        if len(plans) != 1:
            raise RuntimeError('Plan not found')
        return response, data, plans[0]

    def create(
            self,
            url: str,
            image_arch: ImageConfigArch,
    ) -> list[dict]:
        response, data, plan = self.__get_plan()
        versions = [self.__create_version(url, image_arch, plan)]
        for generation in plan['diskGenerations']:
            versions.append(self.__create_version(url, image_arch, generation))
        self.__request(method='PUT', data=data)
        ret = [i for i in versions if i]
        if not ret:
            raise ValueError('No valid generation found for image')
        return ret

    def __create_version(
            self,
            url: str,
            image_arch: ImageConfigArch,
            plan: typing.Any,
    ) -> typing.Optional[dict]:
        plan_id = plan['planId']
        arch = plan['microsoft-azure-corevm.vmImagesArchitecture']
        if image_arch.azure_name != arch:
            return None
        versions = plan['microsoft-azure-corevm.vmImagesPublicAzure']
        versions[self.__name_version] = {
            'description': f'{self.__name_publisher}_{self.__name_offer}_{plan_id}_{self.__name_version}',
            'label': f'{self.__name_publisher}_{self.__name_offer}_{plan_id}',
            'mediaName': f'{self.__name_publisher}_{self.__name_offer}_{plan_id}_{self.__name_version}',
            'osVhdUrl': url,
        }
        return {
            'ref': f'{self.__name_publisher}:{self.__name_offer}:{plan_id}:{self.__name_version}',
            'family_ref': f'{self.__name_publisher}:{self.__name_offer}:{plan_id}:latest',
            'arch': f'{arch}v{plan["microsoft-azure-corevm.generation"]}',
        }
