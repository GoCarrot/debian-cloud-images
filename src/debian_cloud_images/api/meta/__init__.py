# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import typing

from collections import namedtuple
from marshmallow import fields, pre_dump, post_dump, post_load, ValidationError, validates
from uuid import UUID, uuid4

from ..base import SchemaNonempty
from ..registry import registry as _registry
from ...utils.marshmallow import fields_ext


TypeMeta = namedtuple('TypeMeta', ['kind', 'api_version'])


class v1_TypeMetaSchema(SchemaNonempty):
    __model__: typing.ClassVar[typing.Type] = TypeMeta
    __typemeta__: typing.ClassVar[typing.Optional[TypeMeta]] = None

    api_version = fields.Str(data_key='apiVersion')
    kind = fields.Str()

    @post_dump
    def dump_typemeta(self, data: dict, **kw) -> dict:
        if self.__typemeta__:
            data['apiVersion'] = self.__typemeta__.api_version
            data['kind'] = self.__typemeta__.kind
        return data

    @validates('api_version')
    def validate_api_version(self, data: str) -> None:
        if self.__typemeta__ and self.__typemeta__.api_version != data:
            raise ValidationError('Input is of wrong api version')

    @validates('kind')
    def validate_kind(self, data: str) -> None:
        if self.__typemeta__ and self.__typemeta__.kind != data:
            raise ValidationError('Input is of wrong kind')


list_typemeta = TypeMeta('List', 'v1')


@_registry.register
class v1_ListSchema(v1_TypeMetaSchema):
    __model__ = list
    __typemeta__ = list_typemeta

    items = fields_ext.NestedRegistry(many=True)

    @pre_dump
    def dump_items(self, data: list, **kw) -> dict[str, list]:
        return {'items': data}

    @post_load
    def load_items(self, data: dict[str, list], **kw) -> list:
        return data.get('items', [])


class ObjectMeta:
    name: str
    annotations: dict[str, str]
    labels: dict[str, str]
    uid: UUID

    def __init__(
            self,
            name=None,
            annotations=None,
            labels=None,
            uid=None,
    ) -> None:
        self.name = name
        self.annotations = annotations or {}
        self.labels = labels or {}
        self.uid = uid or uuid4()

    def copy(self) -> ObjectMeta:
        return self.__class__(
            name=self.name,
            labels=self.labels.copy(),
        )


class v1_ObjectMetaSchema(SchemaNonempty):
    annotations = fields.Dict(keys=fields.Str(), values=fields.Str())
    name = fields.String()
    labels = fields.Dict(keys=fields.Str(), values=fields.Str())
    uid = fields.UUID()

    @post_load
    def make_object(self, data, **kw):
        return ObjectMeta(**data)
