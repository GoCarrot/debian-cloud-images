# SPDX-License-Identifier: GPL-2.0-or-later

import typing

from marshmallow import Schema, fields, post_load

from ..meta import TypeMeta, v1_ObjectMetaSchema, v1_TypeMetaSchema
from ..registry import registry as _registry


class v1alpha1_ToolConfigAzureAuthSchema(Schema):
    client = fields.UUID()
    secret = fields.Str()


class v1alpha1_ToolConfigAzureCloudpartnerSchema(Schema):
    publisher = fields.Str()
    tenant = fields.UUID()


class v1alpha1_ToolConfigAzureComputegallerySchema(Schema):
    group = fields.Str()
    name = fields.Str()
    subscription = fields.UUID()
    tenant = fields.UUID()


class v1alpha1_ToolConfigAzureImageSchema(Schema):
    group = fields.Str()
    subscription = fields.UUID()
    tenant = fields.UUID()


class v1alpha1_ToolConfigAzureStorageSchema(Schema):
    group = fields.Str()
    name = fields.Str()
    subscription = fields.UUID()
    tenant = fields.UUID()


class v1alpha1_ToolConfigAzureSchema(Schema):
    auth = fields.Nested(v1alpha1_ToolConfigAzureAuthSchema)
    computegallery = fields.Nested(v1alpha1_ToolConfigAzureComputegallerySchema)
    cloudpartner = fields.Nested(v1alpha1_ToolConfigAzureCloudpartnerSchema)
    image = fields.Nested(v1alpha1_ToolConfigAzureImageSchema)
    storage = fields.Nested(v1alpha1_ToolConfigAzureStorageSchema)


class v1alpha1_ToolConfigEc2AuthSchema(Schema):
    key = fields.Str()
    secret = fields.Str()
    token = fields.Str()


class v1alpha1_ToolConfigEc2ImageSchema(Schema):
    regions = fields.List(fields.Str())
    tags = fields.List(fields.Str())


class v1alpha1_ToolConfigEc2StorageSchema(Schema):
    name = fields.Str()


class v1alpha1_ToolConfigEc2SSMSchema(Schema):
    prefix = fields.Str()


class v1alpha1_ToolConfigAwsMarketplaceEntitySchema(Schema):
    id = fields.Str()
    instancetype = fields.Str()


class v1alpha1_ToolConfigAwsMarketplaceListingSchema(Schema):
    releasenotes = fields.Str()
    entities = fields.Dict(fields.Str(), fields.Nested(v1alpha1_ToolConfigAwsMarketplaceEntitySchema))


class v1alpha1_ToolConfigAwsMarketplaceSchema(Schema):
    role = fields.Str()
    api_region = fields.Str()
    listings = fields.Dict(fields.Str(),
                           fields.Nested(v1alpha1_ToolConfigAwsMarketplaceListingSchema))


class v1alpha1_ToolConfigEc2Schema(Schema):
    auth = fields.Nested(v1alpha1_ToolConfigEc2AuthSchema)
    image = fields.Nested(v1alpha1_ToolConfigEc2ImageSchema)
    storage = fields.Nested(v1alpha1_ToolConfigEc2StorageSchema)
    ssm = fields.Nested(v1alpha1_ToolConfigEc2SSMSchema)
    marketplace = fields.Nested(v1alpha1_ToolConfigAwsMarketplaceSchema)


class v1alpha1_ToolConfigGceAuthSchema(Schema):
    credentialsfile = fields.Str()


class v1alpha1_ToolConfigGceImageSchema(Schema):
    project = fields.Str()


class v1alpha1_ToolConfigGceStorageSchema(Schema):
    name = fields.Str()


class v1alpha1_ToolConfigGceSchema(Schema):
    auth = fields.Nested(v1alpha1_ToolConfigGceAuthSchema)
    image = fields.Nested(v1alpha1_ToolConfigGceImageSchema)
    storage = fields.Nested(v1alpha1_ToolConfigGceStorageSchema)


@_registry.register
class v1alpha1_ToolConfigSchema(v1_TypeMetaSchema):
    __typemeta__ = TypeMeta('ToolConfig', 'cloud.debian.org/v1alpha1')

    metadata = fields.Nested(v1_ObjectMetaSchema)
    azure = fields.Nested(v1alpha1_ToolConfigAzureSchema)
    ec2 = fields.Nested(v1alpha1_ToolConfigEc2Schema)
    gce = fields.Nested(v1alpha1_ToolConfigGceSchema)

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> dict[str, typing.Any]:
        data.pop('api_version', None)
        data.pop('kind', None)
        return data
