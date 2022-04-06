import logging

from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

from .s1_item import ImagesAzureComputegalleryItem, ImagesAzureComputegalleryItems


logger = logging.getLogger(__name__)


class ImagesAzureComputegalleryGallery:
    __name_resource_group: str
    __name_gallery: str
    __conn: AzureGenericOAuth2Connection

    def __init__(
            self,
            resource_group: str,
            name: str,
            conn: AzureGenericOAuth2Connection,
    ) -> None:
        self.__name_resource_group = resource_group
        self.__name_gallery = name
        self.__conn = conn

    def items(self) -> ImagesAzureComputegalleryItems:
        return ImagesAzureComputegalleryItems(
            self.__name_resource_group,
            self.__name_gallery,
            self.__conn,
        )

    def get_item(self, name: str) -> ImagesAzureComputegalleryItem:
        return ImagesAzureComputegalleryItem(
            self.__name_resource_group,
            self.__name_gallery,
            name,
            self.__conn,
        )
