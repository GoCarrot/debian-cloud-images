import enum


@enum.unique
class ImagePublicType(enum.Enum):
    dev = {
        'vendor_name': 'debian-{release_id}-{arch}-dev-{version}',
        'vendor_description': '',
    }
    daily = {
        'vendor_name': 'debian-{release_id}-{arch}-daily-{version}',
        'vendor_description': '',
    }
    release = {
        'vendor_name': 'debian-{release_id}-{arch}-{version}',
        'vendor_description': '',
    }


class ImagePublicInfo:
    class ImagePublicInfoApplied:
        def __init__(self, public_type, info):
            self.__public_type, self.__info = public_type, info

        def __getattr__(self, key):
            if not key.startswith('_'):
                return self.__public_type.value[key].format(**self.__info)
            raise KeyError(key)

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
