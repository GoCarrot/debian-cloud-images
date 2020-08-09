from ..publicinfo import ImagePublicInfo
from ...utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


class AzurePartnerInfo:
    public: ImagePublicInfo
    publisher: str
    driver: AzureCloudpartnerOAuth2Connection

    def __init__(
        self,
        public: ImagePublicInfo,
        publisher: str,
        driver: AzureCloudpartnerOAuth2Connection,
    ) -> None:
        self.public = public
        self.publisher = publisher
        self.driver = driver
