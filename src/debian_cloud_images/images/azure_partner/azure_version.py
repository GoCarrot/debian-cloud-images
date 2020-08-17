import collections.abc
import copy
import logging
import typing

from .info import AzurePartnerInfo
from ...utils.azure.image_version import AzureImageVersion


logger = logging.getLogger(__name__)


class AzureVersion:
    _info: AzurePartnerInfo
    _name: AzureImageVersion

    __api_data: typing.Any

    def __init__(self, info: AzurePartnerInfo, name: AzureImageVersion, api_data: typing.Any) -> None:
        self._info = info
        self._name = name

        self.__api_data = api_data

    def __enter__(self) -> 'AzureVersion':
        return self

    def __exit__(self, type, value, tb) -> None:
        pass

    def _rollback(self) -> None:
        pass

    def api_update(self) -> typing.Any:
        return copy.deepcopy(self.__api_data)


class AzureVersions(collections.abc.MutableMapping):
    _info: AzurePartnerInfo
    _children: typing.Dict[str, AzureVersion]

    def __init__(self, info: AzurePartnerInfo, api_data: typing.Any) -> None:
        self._info = info

        generations = {
            g['planId']: g['microsoft-azure-corevm.vmImagesPublicAzure']
            for g in [api_data] + api_data['diskGenerations']
        }

        versions: typing.Dict[str, typing.Dict] = {}
        for generation, images in generations.items():
            for version, image in images.items():
                i = versions.setdefault(AzureImageVersion.from_string(version), {})
                i[generation] = image

        children: typing.Dict[str, AzureVersion] = {}
        for version, images in versions.items():
            # TODO
            children[version] = AzureVersion(info, version, images)

        self._children = children

    def __delitem__(self, name) -> None:
        del self._children[name]

    def __getitem__(self, name) -> AzureVersion:
        return self._children[name]

    def __setitem__(self, name, value) -> None:
        raise NotImplementedError

    def __iter__(self) -> typing.Iterator:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def api_update(self, api_data: typing.Any) -> None:
        generations: typing.Dict[str, typing.Any] = {}

        for name, version in self.items():
            for generation, api_image in version.api_update().items():
                generations.setdefault(generation, {})[str(name)] = api_image

        api_generations = {
            g['planId']: g
            for g in [api_data] + api_data['diskGenerations']
        }

        # TODO: Handle added and removed generations
        for name, g in api_generations.items():
            g['microsoft-azure-corevm.vmImagesPublicAzure'] = generations.pop(name)
        assert not generations
