from marshmallow import Schema, fields, pre_dump, post_load, validate

from ..meta import TypeMeta, v1_TypeMetaSchema
from ..registry import registry as _registry


class ImageConfig:
    def __init__(
        self,
        archs=None,
        releases=None,
        types=None,
        vendors=None,
    ):
        self.archs = archs
        self.releases = releases
        self.types = types
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
        basename=None,
        id=None,
        baseid=None,
        fai_classes=None,
        arch_supports_linux_image_cloud=None,
    ):
        self.name = name
        self.basename = basename
        self.id = id
        self.baseid = baseid
        self.fai_classes = fai_classes
        self.arch_supports_linux_image_cloud = arch_supports_linux_image_cloud


class v1alpha1_ImageConfigReleaseSchema(Schema):
    __model__ = ImageConfigRelease

    name = fields.Str(required=True)
    basename = fields.Str(required=True)
    id = fields.Str(required=True)
    baseid = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    arch_supports_linux_image_cloud = fields.List(fields.Str())

    @post_load
    def load_obj(self, data, **kw):
        return self.__model__(**data)


class ImageConfigType:
    def __init__(
        self,
        name=None,
        fai_classes=None,
        output_name=None,
        output_version=None,
        output_version_azure=None,
    ):
        self.name = name
        self.fai_classes = fai_classes
        self.output_name = output_name
        self.output_version = output_version
        self.output_version_azure = output_version_azure


class v1alpha1_ImageConfigTypeSchema(Schema):
    __model__ = ImageConfigType

    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    output_name = fields.Str(required=True)
    output_version = fields.Str(required=True)
    output_version_azure = fields.Str(required=True)

    @post_load
    def load_obj(self, data, **kw):
        return self.__model__(**data)


class ImageConfigVendorMatch:
    def __init__(
        self,
        op='Enable',
        match_arches=None,
        match_releases=None,
    ):
        self.op = op
        self.match_arches = match_arches
        self.match_releases = match_releases


class v1alpha1_ImageConfigVendorMatchSchema(Schema):
    __model__ = ImageConfigVendorMatch

    op = fields.Str(alidate=validate.OneOf(('Enable', 'Disable')))
    match_arches = fields.List(fields.Str(), data_key='matchArches')
    match_releases = fields.List(fields.Str(), data_key='matchReleases')

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
        matches=None,
    ):
        self.name = name
        self.fai_classes = fai_classes
        self.size = size
        self.use_linux_image_cloud = use_linux_image_cloud
        self.matches = matches


class v1alpha1_ImageConfigVendorSchema(Schema):
    __model__ = ImageConfigVendor

    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    size = fields.Integer(required=True)
    use_linux_image_cloud = fields.Boolean()
    matches = fields.Nested(v1alpha1_ImageConfigVendorMatchSchema, many=True)

    @post_load
    def load_obj(self, data, **kw):
        return self.__model__(**data)


@_registry.register
class v1alpha1_ImageConfigSchema(v1_TypeMetaSchema):
    __model__ = ImageConfig
    __typemeta__ = TypeMeta('ImageConfig', 'cloud.debian.org/v1alpha1')

    _archs_list = fields.Nested(v1alpha1_ImageConfigArchSchema, data_key='archs', many=True)
    _releases_list = fields.Nested(v1alpha1_ImageConfigReleaseSchema, data_key='releases', many=True)
    _types_list = fields.Nested(v1alpha1_ImageConfigTypeSchema, data_key='types', many=True)
    _vendors_list = fields.Nested(v1alpha1_ImageConfigVendorSchema, data_key='vendors', many=True)

    @pre_dump
    def dump_obj(self, obj, **kw):
        data = obj.__dict__.copy()
        data['_archs_list'] = data['archs'].values()
        data['_releases_list'] = data['releases'].values()
        data['_types_list'] = data['types'].values()
        data['_vendors_list'] = data['vendors'].values()
        return data

    @post_load
    def load_obj(self, data, **kw):
        data.pop('api_version', None)
        data.pop('kind', None)
        data['archs'] = {c.name: c for c in data.pop('_archs_list', [])}
        data['releases'] = {c.name: c for c in data.pop('_releases_list', [])}
        data['types'] = {c.name: c for c in data.pop('_types_list', [])}
        data['vendors'] = {c.name: c for c in data.pop('_vendors_list', [])}
        return self.__model__(**data)
