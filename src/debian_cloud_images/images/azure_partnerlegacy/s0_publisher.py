import logging

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzurePartnerlegacyPublisher:
    __name_publisher: str
    __conn: AzureGenericOAuth2Connection

    def __init__(
            self,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_publisher = name
        self.__conn = conn
        raise RuntimeError
