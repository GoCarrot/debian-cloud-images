from ..publicinfo import ImagePublicInfo


class AzurePartnerInfo:
    public: ImagePublicInfo

    def __init__(
        self,
        public: ImagePublicInfo,
    ) -> None:
        self.public = public
