# SPDX-License-Identifier: GPL-2.0-or-later

import enum


@enum.unique
class ImagePublicType(enum.Enum):
    dev = {
        'azure_offer': 'debian-test',
        'azure_sku': '{release_id}',
        'family': 'debian-{release_id}-{vendor}-{arch}-dev-{build_id}',
        'path': '{release}/dev/{build_id}/debian-{release_id}-{vendor}-{arch}-dev-{build_id}-{version}',
        'vendor_family': 'debian-{release_id}-{arch}-dev-{build_id}',
        'vendor_description': 'Debian {release_id} (development build {build_id}-{version})',
    }
    daily = {
        'azure_offer': 'debian-{release_baseid}-daily',
        'azure_sku': '{release_id}',
        'family': 'debian-{release_id}-{vendor}-{arch}-daily',
        'path': '{release}/daily/{version}/debian-{release_id}-{vendor}-{arch}-daily-{version}',
        'vendor_family': 'debian-{release_id}-{arch}-daily',
        'vendor_description': 'Debian {release_id} (daily build {version})',
    }
    release = {
        'azure_offer': 'debian-{release_baseid}',
        'azure_sku': '{release_id}',
        'family': 'debian-{release_id}-{vendor}-{arch}',
        'path': '{release}/{version}/debian-{release_id}-{vendor}-{arch}-{version}',
        'vendor_family': 'debian-{release_id}-{arch}',
        'vendor_description': 'Debian {release_id} ({version})',
    }


class ImagePublicInfo:
    class ImagePublicInfoApplied:
        def __init__(self, public_type, info):
            self.public_type, self.__info = public_type, info

        def __getattr__(self, key):
            if not key.startswith('_'):
                return self.public_type.value[key].format(**self.__info)
            raise KeyError(key)

        @property
        def name(self):
            " Return name "
            return '{}-{}'.format(self.family, self.__info['version'])

        @property
        def vendor_name(self):
            " Return vendor name "
            return '{}-{}'.format(self.vendor_family, self.__info['version'])

        def vendor_name_extra(self, extra: str, length: int = 63) -> str:
            " Return vendor name "
            version = self.__info['version']
            family = self.vendor_family[:length - 2 - len(version) - len(extra)]
            return f'{family}-{version}-{extra}'

        @property
        def vendor_name63(self):
            " Return vendor name limited to 63 characters "
            version = self.__info['version']
            family = self.vendor_family[:63 - 1 - len(version)]
            return f'{family}-{version}'

        @property
        def vendor_azure_family(self):
            " Return vendor family limited to 50 characters for Azure"
            return self.vendor_family[:50]

        @property
        def vendor_gce_family(self):
            " Return vendor family limited to 63 characters for GCE "
            return self.vendor_family[:63]

    def __init__(
        self,
        *,
        override_info={},
        public_type=ImagePublicType.dev,
    ):
        self.__override_info = override_info
        self.public_type = public_type

    def _generate_info(self, info):
        ret = info.copy()
        ret.update(self.__override_info)
        return ret

    def apply(self, info):
        return self.ImagePublicInfoApplied(self.public_type, self._generate_info(info))
