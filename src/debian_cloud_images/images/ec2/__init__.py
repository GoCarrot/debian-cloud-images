import datetime
import logging
import typing

from .s1_cloud_family import StepCloudFamilies
from .s2_cloud_version import StepCloudVersions
from .info import Ec2Info
from ..publicinfo import ImagePublicInfo
from ...utils.libcloud.compute.ec2 import ExEC2NodeDriver
from ...utils.libcloud.storage.s3 import S3BucketStorageDriver


logger = logging.getLogger(__name__)


class Ec2Images:
    __info: Ec2Info

    def __init__(
        self,
        noop: bool,
        public: ImagePublicInfo,
        account: str,
        drivers_compute: typing.Dict[str, ExEC2NodeDriver],
        driver_storage: S3BucketStorageDriver,
    ):
        self.__info = Ec2Info(noop, public, account, drivers_compute, driver_storage)

    def cleanup(self, delete_after: datetime.datetime):
        families = StepCloudFamilies(self.__info)
        families.read()
        self._cleanup_cloud_families(families, delete_after)

    def _cleanup_cloud_families(self, families: StepCloudFamilies, delete_after: datetime.datetime) -> None:
        for name, family in sorted(families.items()):
            logger.debug(f'Handle cloud family {name!r}')
            with family as family:
                self._cleanup_cloud_versions(family.versions, delete_after, name)

    def _cleanup_cloud_versions(self, versions: StepCloudVersions, delete_after: datetime.datetime, name_family: str) -> None:
        versions_all = frozenset(versions.keys())
        versions_remain = set()

        for version in sorted(versions_all, reverse=True):
            if version.date is None:
                logger.warning(f'Not deleting images from {name_family}, undated images found')
                return

            if version.date >= delete_after:
                logging.debug(f'Not deleting image {version} from {name_family}, too new')
                versions_remain.add(version)
            elif not versions_remain:
                logging.debug(f'Not deleting image {version} from {name_family}, last remaining')
                versions_remain.add(version)
            else:
                break

        for version in sorted(versions_all - versions_remain):
            logging.info(f'Deleting image {version} from {name_family}')
            del versions[version]
