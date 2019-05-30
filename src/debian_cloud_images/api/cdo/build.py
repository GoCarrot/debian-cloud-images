from marshmallow import Schema, fields, pre_dump, post_load

from ..meta import ObjectMeta, TypeMeta, v1_ObjectMetaSchema, v1_TypeMetaSchema
from ..registry import registry as _registry


class Build:
    def __init__(self, info=None, packages=None, metadata=None):
        self.info = info
        self.packages = packages
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
    def dump_items(self, data):
        return {'metadata': data.metadata, 'data': data}

    @post_load
    def load_obj(self, data):
        return self.__model__(metadata=data['metadata'], **data['data'])
