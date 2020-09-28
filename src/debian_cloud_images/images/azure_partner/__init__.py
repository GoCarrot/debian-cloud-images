import datetime
import itertools
import logging
import typing

from .azure_offer import AzureOffers
from .azure_sku import AzureSkus
from .azure_version import AzureVersions
from .info import AzurePartnerInfo
from ..publicinfo import ImagePublicInfo
from ...utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


logger = logging.getLogger(__name__)


class AzurePartnerImages:
    __info: AzurePartnerInfo

    def __init__(
        self,
        noop: bool,
        public: ImagePublicInfo,
        publisher: str,
        driver: AzureCloudpartnerOAuth2Connection,
    ):
        self.__info = AzurePartnerInfo(noop, public, publisher, driver)

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

    def cleanup(self, names: typing.List[str], delete_after: datetime.datetime):
        offers = AzureOffers(self.__info)
        self._cleanup_offers(offers, names, delete_after)

    def _cleanup_offers(self, offers: AzureOffers, names: typing.List[str], delete_after: datetime.datetime) -> None:
        for name in names:
            logger.debug(f'Handle Azure offer {name!r}')
            with offers[name] as f:
                self._cleanup_skus(f.skus, delete_after, name)
                if not self.__info.noop:
                    logging.info(f'Save offer {name}')
                    f.commit()

    def _cleanup_skus(self, skus: AzureSkus, delete_after: datetime.datetime, name_offer: str) -> None:
        for name, sku in skus.items():
            logger.debug(f'Handle Azure sku {name!r} (offer {name_offer!r})')
            with sku as f:
                self._cleanup_versions(f.versions, delete_after, name_offer, name)

    def _cleanup_versions(self, versions: AzureVersions, delete_after: datetime.datetime, name_offer: str, name_sku: str) -> None:
        versions_all = frozenset(versions.keys())
        versions_remain = set()

        for version in sorted(versions_all, reverse=True):
            if version.minor == 0:
                logger.warning(f'Not deleting images from {name_offer}/{name_sku}, undated images found')
                return

            date = datetime.datetime.strptime(str(version.minor), '%Y%m%d')
            if date >= delete_after:
                logging.debug(f'Not deleting image {version} from {name_offer}/{name_sku}, too new')
                versions_remain.add(version)
            elif not versions_remain:
                logging.debug(f'Not deleting image {version} from {name_offer}/{name_sku}, last remaining')
                versions_remain.add(version)
            else:
                break

        for version in sorted(versions_all - versions_remain):
            logging.info(f'Deleting image {version} from {name_offer}/{name_sku}')
            del versions[version]

    def _group(self, images: typing.List, key: typing.Callable) -> typing.Iterator:
        return itertools.groupby(sorted(images, key=key), key=key)

    def _group_key_offers(self, image) -> str:
        return self.__info.public.apply(image.build_info).azure_offer

    def _group_key_skus(self, image) -> str:
        return self.__info.public.apply(image.build_info).azure_sku

    def _group_key_versions(self, image) -> str:
        return image.build_info['version_azure']
