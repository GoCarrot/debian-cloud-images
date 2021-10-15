from marshmallow import fields, post_load

from ..meta import TypeMeta, v1_TypeMetaSchema
from ..registry import registry as _registry


class ImageConfig:
    def __init__(
        self,
    ):
        pass


@_registry.register
class v1alpha1_ImageConfigSchema(v1_TypeMetaSchema):
    __model__ = ImageConfig
    __typemeta__ = TypeMeta('ImageConfig', 'cloud.debian.org/v1alpha1')

    @post_load
    def load_obj(self, data, **kw):
        data.pop('api_version', None)
        data.pop('kind', None)
        return self.__model__(**data)
