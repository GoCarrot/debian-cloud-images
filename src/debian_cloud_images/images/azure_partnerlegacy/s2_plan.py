import logging

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzurePartnerlegacyPlan:
    __name_publisher: str
    __name_offer: str
    __name_plan: str
    __conn: AzureGenericOAuth2Connection

    def __init__(
            self,
            publisher: str,
            offer: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_publisher = publisher
        self.__name_offer = offer
        self.__name_plan = name
        self.__conn = conn
        raise RuntimeError
