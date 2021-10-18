from marshmallow import Schema, fields, pre_dump, post_load

from ..meta import TypeMeta, v1_TypeMetaSchema
from ..registry import registry as _registry


class ImageConfig:
    def __init__(
        self,
        archs=None,
        releases=None,
        vendors=None,
    ):
        self.archs = archs
        self.releases = releases
        self.vendors = vendors


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


class ImageConfigRelease:
    def __init__(
        self,
        name=None,
        id=None,
        baseid=None,

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


class ImageConfigVendor:
    def __init__(
        self,
        name=None,
        fai_classes=None,
        size=None,
        use_linux_image_cloud=False,
    ):
        self.name = name
        self.fai_classes = fai_classes
        self.size = size
        self.use_linux_image_cloud = use_linux_image_cloud


class v1alpha1_ImageConfigVendorSchema(Schema):
    __model__ = ImageConfigVendor

    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    size = fields.Integer(required=True)
    use_linux_image_cloud = fields.Boolean()

    @post_load
    def load_obj(self, data, **kw):
        return self.__model__(**data)


@_registry.register
class v1alpha1_ImageConfigSchema(v1_TypeMetaSchema):
    __model__ = ImageConfig
    __typemeta__ = TypeMeta('ImageConfig', 'cloud.debian.org/v1alpha1')

    _archs_list = fields.Nested(v1alpha1_ImageConfigArchSchema, data_key='archs', many=True)
    _vendors_list = fields.Nested(v1alpha1_ImageConfigVendorSchema, data_key='vendors', many=True)

    @pre_dump
    def dump_obj(self, obj, **kw):
        data = obj.__dict__.copy()
        data['_archs_list'] = data['archs'].values()
        data['_vendors_list'] = data['vendors'].values()
        return data

    @post_load
    def load_obj(self, data, **kw):
        data.pop('api_version', None)
        data.pop('kind', None)
        data['archs'] = {c.name: c for c in data.pop('_archs_list', [])}
        data['vendors'] = {c.name: c for c in data.pop('_vendors_list', [])}
        return self.__model__(**data)
