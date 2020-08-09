import itertools
import logging
import typing

from .azure_offer import AzureOffers
from .azure_sku import AzureSkus
from .azure_version import AzureVersions
from .info import AzurePartnerInfo
from ..publicinfo import ImagePublicInfo


logger = logging.getLogger(__name__)


class AzurePartnerImages:
    __info: AzurePartnerInfo

    def __init__(
        self,
        public: ImagePublicInfo,
    ):
        self.__info = AzurePartnerInfo(public)

    def add(self, images: typing.List) -> None:
        offers = AzureOffers(self.__info)
        self._add_offers(offers, images)

    def _add_offers(self, offers: AzureOffers, images: typing.List) -> None:
        for name, images_grouped in self._group(images, self._group_key_offers):
            logger.debug(f'Handle Azure offer {name!r}')
            with offers[name] as f:
                self._add_skus(f.skus, images_grouped)

    def _add_skus(self, skus: AzureSkus, images: typing.List) -> None:
        for name, images_grouped in self._group(images, self._group_key_skus):
            logger.debug(f'Handle Azure sku {name!r}')
            with skus[name] as f:
                self._add_versions(f.versions, images_grouped)

    def _add_versions(self, versions: AzureVersions, images: typing.List) -> None:
        for name, images_grouped in self._group(images, self._group_key_versions):
            logger.debug(f'Handle Azure version {name!r}')
            with versions[name] as f:
                raise NotImplementedError(f)

    def cleanup(self, *names):
        offers = AzureOffers(self.__info)
        self._cleanup_offers(offers, names)

    def _cleanup_offers(self, offers: AzureOffers, names: typing.List) -> None:
        for name in names:
            logger.debug(f'Handle Azure offer {name!r}')
            with offers[name] as f:
                self._cleanup_skus(f.skus)

    def _cleanup_skus(self, skus: AzureSkus) -> None:
        for name, sku in skus.items():
            logger.debug(f'Handle Azure sku {name!r}')
            with sku as f:
                self._cleanup_versions(f.versions)

    def _cleanup_versions(self, versions: AzureVersions) -> None:
        raise NotImplementedError(versions)

    def _group(self, images: typing.List, key: typing.Callable) -> typing.Iterator:
        return itertools.groupby(sorted(images, key=key), key=key)

    def _group_key_offers(self, image) -> str:
        return self.__info.public.apply(image.build_info).azure_offer

    def _group_key_skus(self, image) -> str:
        return self.__info.public.apply(image.build_info).azure_sku

    def _group_key_versions(self, image) -> str:
        return image.build_info['version_azure']
