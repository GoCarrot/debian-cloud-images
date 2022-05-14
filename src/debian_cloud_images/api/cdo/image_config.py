import typing

from marshmallow import Schema, fields, pre_dump, post_load, validate

from ..meta import TypeMeta, v1_TypeMetaSchema
from ..registry import registry as _registry


class ImageConfig:
    def __init__(
        self,
        archs=None,
        public_types=None,
        releases=None,
        types=None,
        vendors=None,
    ):
        self.archs = archs
        self.public_types = public_types
        self.releases = releases
        self.types = types
        self.vendors = vendors


class ImageConfigMatch:
    def __init__(
        self,
        op='Enable',
        match_arches=None,
        match_releases=None,
        match_vendors=None,
        upload_group=None,
    ):
        self.op = op
        self.match_arches = match_arches
        self.match_releases = match_releases
        self.match_vendors = match_vendors
        self.upload_group = upload_group


class v1alpha1_ImageConfigMatchSchema(Schema):
    op = fields.Str(validate=validate.OneOf(('Enable', 'EnableUpload', 'Disable', 'DisableUpload')))
    match_arches = fields.List(fields.Str(), data_key='matchArches')
    match_releases = fields.List(fields.Str(), data_key='matchReleases')
    match_vendors = fields.List(fields.Str(), data_key='matchVendors')
    upload_group = fields.Str(data_key='uploadGroup')

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigMatch:
        return ImageConfigMatch(**data)


class ImageConfigArch:
    def __init__(
        self,
        name=None,
        azure_name=None,
        fai_classes=None,
    ):
        self.name = name
        self.azure_name = azure_name
        self.fai_classes = fai_classes


class v1alpha1_ImageConfigArchSchema(Schema):
    name = fields.Str(required=True)
    azure_name = fields.Str(data_key='azureName')
    fai_classes = fields.List(fields.Str())

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigArch:
        return ImageConfigArch(**data)


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
    name = fields.Str(required=True)
    basename = fields.Str(required=True)
    id = fields.Str(required=True)
    baseid = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    arch_supports_linux_image_cloud = fields.List(fields.Str())

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigRelease:
        return ImageConfigRelease(**data)


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
    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    output_name = fields.Str(required=True)
    output_version = fields.Str(required=True)
    output_version_azure = fields.Str(required=True)

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigType:
        return ImageConfigType(**data)


class ImageConfigPublicType:
    def __init__(
        self,
        name=None,
        matches=None,
    ):
        self.name = name
        self.matches = matches


class v1alpha1_ImageConfigPublicTypeSchema(Schema):
    name = fields.Str(required=True)
    matches = fields.Nested(v1alpha1_ImageConfigMatchSchema, many=True)

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigPublicType:
        return ImageConfigPublicType(**data)


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
    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str())
    size = fields.Integer(required=True)
    use_linux_image_cloud = fields.Boolean()
    matches = fields.Nested(v1alpha1_ImageConfigMatchSchema, many=True)

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigVendor:
        return ImageConfigVendor(**data)


@_registry.register
class v1alpha1_ImageConfigSchema(v1_TypeMetaSchema):
    __model__ = ImageConfig
    __typemeta__ = TypeMeta('ImageConfig', 'cloud.debian.org/v1alpha1')

    _archs_list = fields.Nested(v1alpha1_ImageConfigArchSchema, data_key='archs', many=True)
    _public_types_list = fields.Nested(v1alpha1_ImageConfigPublicTypeSchema, data_key='publicTypes', many=True)
    _releases_list = fields.Nested(v1alpha1_ImageConfigReleaseSchema, data_key='releases', many=True)
    _types_list = fields.Nested(v1alpha1_ImageConfigTypeSchema, data_key='types', many=True)
    _vendors_list = fields.Nested(v1alpha1_ImageConfigVendorSchema, data_key='vendors', many=True)

    @pre_dump
    def dump_obj(self, obj: dict[str, typing.Any], **kw) -> dict[str, typing.Any]:
        data = obj.__dict__.copy()
        data['_archs_list'] = data['archs'].values()
        data['_public_types_list'] = data['public_types'].values()
        data['_releases_list'] = data['releases'].values()
        data['_types_list'] = data['types'].values()
        data['_vendors_list'] = data['vendors'].values()
        return data

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfig:
        data.pop('api_version', None)
        data.pop('kind', None)
        data['archs'] = {c.name: c for c in data.pop('_archs_list', [])}
        data['public_types'] = {c.name: c for c in data.pop('_public_types_list', [])}
        data['releases'] = {c.name: c for c in data.pop('_releases_list', [])}
        data['types'] = {c.name: c for c in data.pop('_types_list', [])}
        data['vendors'] = {c.name: c for c in data.pop('_vendors_list', [])}
        return ImageConfig(**data)
