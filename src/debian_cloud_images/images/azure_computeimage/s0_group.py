import logging

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection


logger = logging.getLogger(__name__)


class ImagesAzureComputeimageGroup:
    __name_resource_group: str
    __conn: AzureGenericOAuth2Connection

    def __init__(
            self,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_resource_group = name
        self.__conn = conn
        raise RuntimeError
