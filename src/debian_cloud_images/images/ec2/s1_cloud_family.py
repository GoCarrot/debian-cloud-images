import collections.abc
import logging
import typing

from .s2_cloud_version import StepCloudVersions
from .info import Ec2Info
from ...utils.image_version import ImageVersion


logger = logging.getLogger(__name__)


class StepCloudFamily:
    name: str
    versions: StepCloudVersions

    _info: Ec2Info

    def __init__(self, info: Ec2Info, name: str) -> None:
        self._info = info
        self.name = name

        self.versions = StepCloudVersions(self._info)

    def __enter__(self) -> 'StepCloudFamily':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass


class StepCloudFamilies(collections.abc.Mapping):
    _info: Ec2Info
    _children: typing.Dict[str, StepCloudFamily]

    def __init__(self, info: Ec2Info) -> None:
        self._info = info
        self._children = {}

    def __getitem__(self, name) -> StepCloudFamily:
        return self._children[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def setdefault(self, name: str) -> StepCloudFamily:
        return self._children.setdefault(name, StepCloudFamily(self._info, name))

    def read(self) -> None:
        for region, driver in sorted(self._info.drivers_compute.items()):
            logger.debug(f'Reading from region {region}')

            for image in driver.list_images(ex_owner=self._info.account):
                tags = image.extra['tags']
                family = tags.get('ImageFamily', None)
                version = tags.get('ImageVersion', None)
                if family and version:
                    v = self.setdefault(family).versions.setdefault(ImageVersion.from_string(version))
                    v.images[region] = image
                else:
                    logger.warning(f'Found image {image.name} without proper tags in region {region}')

            for snapshot in driver.list_snapshots(owner=self._info.account):
                tags = snapshot.extra['tags']
                family = tags.get('ImageFamily', None)
                version = tags.get('ImageVersion', None)
                if family and version:
                    v = self.setdefault(family).versions.setdefault(ImageVersion.from_string(version))
                    v.snapshots[region] = snapshot
                else:
                    logger.warning(f'Found snapshot {snapshot.id} without proper tags in region {region}')
