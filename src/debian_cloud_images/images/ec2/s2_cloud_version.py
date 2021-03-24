import collections.abc
import logging
import typing

from .info import Ec2Info
from ...utils.image_version import ImageVersion


logger = logging.getLogger(__name__)


class StepCloudVersion:
    _info: Ec2Info
    _name: ImageVersion

    images: typing.Dict[str, typing.Any]
    snapshots: typing.Dict[str, typing.Any]

    def __init__(self, info: Ec2Info, name: ImageVersion) -> None:
        self._info = info
        self._name = name

        self.images = {}
        self.snapshots = {}

    def __enter__(self) -> 'StepCloudVersion':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass

    def delete(self) -> None:
        for region, image in sorted(self.images.items()):
            if not self._info.noop:
                logger.debug(f'Deleting image {image.name} from region {region}')
                image.driver.delete_image(image)
            else:
                logger.info(f'Would deleting image {image.name} from region {region}')

        for region, snapshot in sorted(self.snapshots.items()):
            image_name = snapshot.extra['tags']['AMI']
            if not self._info.noop:
                logger.debug(f'Deleting snapshot {snapshot.id} for image {image_name} from region {region}')
                snapshot.driver.destroy_volume_snapshot(snapshot)
            else:
                logger.info(f'Would deleting snapshot {snapshot.id} for image {image_name} from region {region}')


class StepCloudVersions(collections.abc.Mapping):
    _info: Ec2Info
    _children: typing.Dict[ImageVersion, StepCloudVersion]

    def __init__(self, info: Ec2Info) -> None:
        self._info = info
        self._children = {}

    def __delitem__(self, name: ImageVersion) -> None:
        self._children[name].delete()
        del self._children[name]

    def __getitem__(self, name: ImageVersion) -> StepCloudVersion:
        return self._children[name]

    def __iter__(self) -> typing.Iterator[ImageVersion]:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def setdefault(self, name: ImageVersion) -> StepCloudVersion:
        return self._children.setdefault(name, StepCloudVersion(self._info, name))
