from __future__ import annotations

import collections.abc
import logging
import typing

from .info import PublicInfo
from .s2_cloud_version import StepCloudVersions


logger = logging.getLogger(__name__)


class StepDebianRelease:
    name: str
    version: StepCloudVersions

    _info: PublicInfo

    def __init__(self, info: PublicInfo, name: str) -> None:
        self._info = info
        self.name = name

    def __enter__(self) -> StepDebianRelease:
        if not self._info.path.is_dir():
            raise RuntimeError(f'Storage path {self._info.path} does not exist, please create first')

        pathrelease = self._info.path / self.name
        pathrelease.mkdir(exist_ok=True)

        if self._info.public_type != 'release':
            path = pathrelease / self._info.public_type
            path.mkdir(exist_ok=True)
            ref = self.name + '/' + self._info.public_type + '/'
        else:
            path = pathrelease
            ref = self.name + '/'

        self.versions = StepCloudVersions(self._info, path, ref)

        return self

    def __exit__(self, type, value, tb) -> None:
        del self.versions


class StepDebianReleases(collections.abc.Mapping):
    _info: PublicInfo
    _children: typing.Dict[str, StepDebianRelease]

    def __init__(self, info: PublicInfo) -> None:
        self._info = info
        self._children = {}

    def __getitem__(self, name) -> StepDebianRelease:
        return self._children[name]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def setdefault(self, name: str) -> StepDebianRelease:
        return self._children.setdefault(name, StepDebianRelease(self._info, name))
