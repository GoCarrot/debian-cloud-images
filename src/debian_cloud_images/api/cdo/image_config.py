from marshmallow import Schema, fields, pre_dump, post_load

from ..meta import TypeMeta, v1_TypeMetaSchema
from ..registry import registry as _registry


class ImageConfig:
    def __init__(
        self,
        archs=None,
    ):
        self.archs = archs


class ImageConfigArch:
    def __init__(
        self,
        name=None,
        fai_classes=None,
    ):
        self.name = name
        self.fai_classes = fai_classes


class v1alpha1_ImageConfigArchSchema(Schema):
    __model__ = ImageConfigArch

    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())

    @post_load
    def load_obj(self, data, **kw):
        return self.__model__(**data)


@_registry.register
class v1alpha1_ImageConfigSchema(v1_TypeMetaSchema):
    __model__ = ImageConfig
    __typemeta__ = TypeMeta('ImageConfig', 'cloud.debian.org/v1alpha1')

    _archs_list = fields.Nested(v1alpha1_ImageConfigArchSchema, data_key='archs', many=True)

    @pre_dump
    def dump_obj(self, obj, **kw):
        data = obj.__dict__.copy()
        data['_archs_list'] = data['archs'].values()
        return data

    @post_load
    def load_obj(self, data, **kw):
        data.pop('api_version', None)
        data.pop('kind', None)
        data['archs'] = {c.name: c for c in data.pop('_archs_list', [])}
        return self.__model__(**data)
