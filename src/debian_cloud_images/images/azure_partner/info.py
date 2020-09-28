from ..publicinfo import ImagePublicInfo
from ...utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


class AzurePartnerInfo:
    noop: bool
    public: ImagePublicInfo
    publisher: str
    driver: AzureCloudpartnerOAuth2Connection

    def __init__(
        self,
        noop: bool,
        public: ImagePublicInfo,
        publisher: str,
        driver: AzureCloudpartnerOAuth2Connection,
    ) -> None:
        self.noop = noop
        self.public = public
        self.publisher = publisher
        self.driver = driver
