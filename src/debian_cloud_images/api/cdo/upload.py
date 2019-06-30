from marshmallow import Schema, fields, pre_dump, post_load

from ..meta import ObjectMeta, TypeMeta, v1_ObjectMetaSchema, v1_TypeMetaSchema
from ..registry import registry as _registry


class Upload:
    def __init__(self, provider, ref, family_ref=None, metadata=None):
        self.provider = provider
        self.ref = ref
        self.family_ref = family_ref
        self.metadata = metadata or ObjectMeta()


class v1alpha1_UploadDataSchema(Schema):
    family_ref = fields.Str(data_key='familyRef')
    provider = fields.Str(required=True)
    ref = fields.Str(required=True)


@_registry.register
class v1alpha1_UploadSchema(v1_TypeMetaSchema):
    __model__ = Upload
    __typemeta__ = TypeMeta('Upload', 'cloud.debian.org/v1alpha1')

    metadata = fields.Nested(v1_ObjectMetaSchema, required=True)
    data = fields.Nested(v1alpha1_UploadDataSchema)

    @pre_dump
    def dump_items(self, data, **kw):
        return {'metadata': data.metadata, 'data': data}

    @post_load
    def load_obj(self, data, **kw):
        return self.__model__(metadata=data['metadata'], **data['data'])
