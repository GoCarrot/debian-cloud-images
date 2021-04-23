import datetime
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
            family = self.__info.public.apply(image.build_info).family
            with step.add(name, family) as f:
                f.write(image)

    def cleanup(self, delete_after: datetime.datetime, releases: typing.List[str]) -> None:
        step = StepDebianReleases(self.__info)
        self._cleanup_debian_releases(step, delete_after, releases)

    def _cleanup_debian_releases(self, step: StepDebianReleases, delete_after: datetime.datetime, releases: typing.List[str]) -> None:
        for name in releases:
            logger.debug(f'Handle Debian release {name!r}')
            with step.setdefault(name) as f:
                self._cleanup_cloud_versions(f.versions, delete_after, name)

    def _cleanup_cloud_versions(self, versions: StepCloudVersions, delete_after: datetime.datetime, name: str) -> None:
        versions.read()
        versions_all = frozenset(versions.keys())
        versions_remain = set()

        for version in sorted(versions_all, reverse=True):
            if version.date is None:
                logger.warning(f'Not deleting images from {name}, undated images found')
                return

            if version.date >= delete_after:
                logging.debug(f'Not deleting image {version} from {name}, too new')
                versions_remain.add(version)
            elif not versions_remain:
                logging.debug(f'Not deleting image {version} from {name}, last remaining')
                versions_remain.add(version)
            else:
                break

        for version in sorted(versions_all - versions_remain):
            logging.info(f'Deleting image {version} from {name}')
            del versions[version]

    def _group(self, images: typing.List, key: typing.Callable) -> typing.Iterator:
        return itertools.groupby(sorted(images, key=key), key=key)

    def _group_key_releases(self, image) -> str:
        return image.build_release

    def _group_key_versions(self, image) -> str:
        return image.build_version
