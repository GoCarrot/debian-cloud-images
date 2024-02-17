# SPDX-License-Identifier: GPL-2.0-or-later

import dataclasses
import typing

from marshmallow import Schema, fields, pre_dump, post_load

from ..meta import ObjectMeta, TypeMeta, v1_ObjectMetaSchema, v1_TypeMetaSchema
from ..registry import registry as _registry


@dataclasses.dataclass
class Upload:
    provider: str
    ref: str
    family_ref: typing.Optional[str] = dataclasses.field(default=None)
    metadata: ObjectMeta = dataclasses.field(default_factory=ObjectMeta)


class v1alpha1_UploadDataSchema(Schema):
    family_ref = fields.Str(data_key='familyRef', allow_none=True)
    provider = fields.Str(required=True)
    ref = fields.Str(required=True)


@_registry.register
class v1alpha1_UploadSchema(v1_TypeMetaSchema):
    __model__ = Upload
    __typemeta__ = TypeMeta('Upload', 'cloud.debian.org/v1alpha1')

    metadata = fields.Nested(v1_ObjectMetaSchema, required=True)
    data = fields.Nested(v1alpha1_UploadDataSchema)

    @pre_dump
    def dump_items(self, data: Upload, **kw) -> dict[str, typing.Any]:
        return {'metadata': data.metadata, 'data': data}

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> Upload:
        return Upload(metadata=data['metadata'], **data['data'])
