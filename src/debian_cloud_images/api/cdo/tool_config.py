from marshmallow import Schema, fields, post_load

from ..meta import TypeMeta, v1_ObjectMetaSchema, v1_TypeMetaSchema
from ..registry import registry as _registry


class v1alpha1_ToolConfigAzureCloudpartnerSchema(Schema):
    publisher = fields.Str()


class v1alpha1_ToolConfigAzureSchema(Schema):
    cloudpartner = fields.Nested(v1alpha1_ToolConfigAzureCloudpartnerSchema)


class v1alpha1_ToolConfigEc2Schema(Schema):
    bucket = fields.Str()


class v1alpha1_ToolConfigGceSchema(Schema):
    bucket = fields.Str()
    credentials_file = fields.Str(data_key='credentialsFile')
    project = fields.Str()


@_registry.register
class v1alpha1_ToolConfigSchema(v1_TypeMetaSchema):
    __typemeta__ = TypeMeta('ToolConfig', 'cloud.debian.org/v1alpha1')

    metadata = fields.Nested(v1_ObjectMetaSchema)
    azure = fields.Nested(v1alpha1_ToolConfigAzureSchema)
    ec2 = fields.Nested(v1alpha1_ToolConfigEc2Schema)
    gce = fields.Nested(v1alpha1_ToolConfigGceSchema)

    @post_load
    def load_obj(self, data, **kw):
        data.pop('api_version', None)
        data.pop('kind', None)
        return data
