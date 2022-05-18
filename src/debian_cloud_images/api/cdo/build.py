import typing

from marshmallow import Schema, fields, pre_dump, post_load

from ..meta import ObjectMeta, TypeMeta, v1_ObjectMetaSchema, v1_TypeMetaSchema
from ..registry import registry as _registry


class Build:
    info: dict
    packages: list
    metadata: ObjectMeta

    def __init__(
            self,
            info: typing.Optional[dict] = None,
            packages: typing.Optional[list] = None,
            metadata: typing.Optional[ObjectMeta] = None,
    ):
        self.info = info or {}
        self.packages = packages or []
        self.metadata = metadata or ObjectMeta()


class v1alpha1_BuildDataPackageSchema(Schema):
    name = fields.Str(required=True)
    version = fields.Str(required=True)


class v1alpha1_BuildDataSchema(Schema):
    info = fields.Dict(keys=fields.Str(), values=fields.Str())
    packages = fields.Nested(v1alpha1_BuildDataPackageSchema, many=True)


@_registry.register
class v1alpha1_BuildSchema(v1_TypeMetaSchema):
    __model__ = Build
    __typemeta__ = TypeMeta('Build', 'cloud.debian.org/v1alpha1')

    metadata = fields.Nested(v1_ObjectMetaSchema, required=True)
    data = fields.Nested(v1alpha1_BuildDataSchema)

    @pre_dump
    def dump_items(self, data: Build, **kw) -> dict[str, typing.Any]:
        return {'metadata': data.metadata, 'data': data}

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> Build:
        return Build(metadata=data['metadata'], **data['data'])
