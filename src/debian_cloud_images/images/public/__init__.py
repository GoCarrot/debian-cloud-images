import itertools
import logging
import pathlib
import typing

from ..publicinfo import ImagePublicInfo

from .info import PublicInfo
from .s1_debian_release import StepDebianReleases
from .s2_cloud_version import StepCloudVersions
from .s3_cloud_image import StepCloudImages


logger = logging.getLogger(__name__)


class PublicImages:
    __info: PublicInfo

    def __init__(
        self,
        noop: bool,
        public: ImagePublicInfo,
        public_type: str,
        path: pathlib.Path,
        provider: str,
    ):
        self.__info = PublicInfo(noop, public, public_type, path, provider)

    def add(self, images: typing.List) -> None:
        step = StepDebianReleases(self.__info)
        self._add_releases(step, images)

    def _add_releases(self, step: StepDebianReleases, images: typing.List) -> None:
        for name, images_grouped in self._group(images, self._group_key_releases):
            logger.debug(f'Handle Debian release {name!r}')
            with step.setdefault(name) as f:
                self._add_versions(f.versions, images_grouped)

    def _add_versions(self, step: StepCloudVersions, images: typing.List) -> None:
        for name, images_grouped in self._group(images, self._group_key_versions):
            logger.debug(f'Handle cloud version {name!r}')
            with step.add(name) as f:
                self._add_images(f.images, images_grouped)

    def _add_images(self, step: StepCloudImages, images: typing.List) -> None:
        for image in images:
            name = self.__info.public.apply(image.build_info).name
            with step.add(name) as f:
                f.write(image)

    def _group(self, images: typing.List, key: typing.Callable) -> typing.Iterator:
        return itertools.groupby(sorted(images, key=key), key=key)

    def _group_key_releases(self, image) -> str:
        return image.build_release

    def _group_key_versions(self, image) -> str:
        return image.build_version
