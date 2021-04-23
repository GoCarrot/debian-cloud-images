import pathlib

from ..publicinfo import ImagePublicInfo


class PublicInfo:
    noop: bool
    public: ImagePublicInfo
    public_type: str
    path: pathlib.Path
    provider: str

    def __init__(
        self,
        noop: bool,
        public: ImagePublicInfo,
        public_type: str,
        path: pathlib.Path,
        provider: str,
    ) -> None:
        self.noop = noop
        self.public = public
        self.public_type = public_type
        self.path = path
        self.provider = provider
