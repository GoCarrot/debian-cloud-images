import logging

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzurePartnerlegacyOffer:
    __name_publisher: str
    __name_offer: str
    __conn: AzureGenericOAuth2Connection

    def __init__(
            self,
            publisher: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_publisher = publisher
        self.__name_offer = name
        self.__conn = conn
        raise RuntimeError
