# SPDX-License-Identifier: GPL-2.0-or-later

import collections.abc
import libcloud
import logging
import re
import typing

from os import getenv
from time import sleep
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

    # Deregister an AMI, retrying the operation on internal service errors
    def _delete_image(self, image, tries_remaining=5):
        tries_remaining = tries_remaining - 1
        retry_codes = re.compile("ServerInternal|InternalFailure|RequestLimitExceeded|InternalError")
        try:
            image.driver.delete_image(image)
        except libcloud.common.exceptions.BaseHTTPError as e:
            if tries_remaining <= 0:
                raise e
            elif retry_codes.match(e.args[0]):
                if not getenv("NO_RETRY_DELAY") == "true":
                    sleep(10 - 2 * tries_remaining)
                self._delete_image(image, tries_remaining)
            else:
                raise e

    # Delete a snapshot, retrying the operation on internal service errors
    def _delete_snapshot(self, snapshot, tries_remaining=5):
        tries_remaining = tries_remaining - 1
        retry_codes = re.compile("ServerInternal|InternalFailure|RequestLimitExceeded|InternalError")
        try:
            snapshot.driver.destroy_volume_snapshot(snapshot)
        except libcloud.common.exceptions.BaseHTTPError as e:
            if tries_remaining <= 0:
                raise e
            elif retry_codes.match(e.args[0]):
                if not getenv("NO_RETRY_DELAY") == "true":
                    sleep(10 - 2 * tries_remaining)
                self._delete_snapshot(snapshot, tries_remaining)
            else:
                raise e

    def delete(self) -> None:
        for region, image in sorted(self.images.items()):
            if not self._info.noop:
                logger.debug(f'Deleting image {image.name} from region {region}')
                self._delete_image(image)
            else:
                logger.info(f'Would delete image {image.name} from region {region}')

        for region, snapshot in sorted(self.snapshots.items()):
            image_name = snapshot.extra['tags']['AMI']
            if not self._info.noop:
                logger.debug(f'Deleting snapshot {snapshot.id} for image {image_name} from region {region}')
                try:
                    self._delete_snapshot(snapshot)
                except libcloud.common.exceptions.BaseHTTPError as e:
                    if e.args[0].find('InvalidSnapshot.') != -1:
                        logging.warning(f'Skipping snapshot deletion: {e}')
                    else:
                        raise e
            else:
                logger.info(f'Would delete snapshot {snapshot.id} for image {image_name} from region {region}')


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
