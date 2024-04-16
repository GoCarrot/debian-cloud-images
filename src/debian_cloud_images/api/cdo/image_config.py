# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import dataclasses
import typing

from marshmallow import Schema, fields, pre_dump, post_load, validate

from ..meta import TypeMeta, v1_TypeMetaSchema
from ..registry import registry as _registry


@dataclasses.dataclass
class ImageConfig:
    archs: list[ImageConfigArch]
    public_types: list[ImageConfigPublicType]
    releases: list[ImageConfigRelease]
    types: list[ImageConfigType]
    vendors: list[ImageConfigVendor]


@dataclasses.dataclass
class ImageConfigMatch:
    op: str = dataclasses.field(default='Enable')
    match_arches: list[str] = dataclasses.field(default_factory=list)
    match_releases: list[str] = dataclasses.field(default_factory=list)
    match_vendors: list[str] = dataclasses.field(default_factory=list)
    upload_group: typing.Optional[str] = dataclasses.field(default=None)


class v1alpha1_ImageConfigMatchSchema(Schema):
    op = fields.Str(validate=validate.OneOf(('Enable', 'EnableUpload', 'Disable', 'DisableUpload')))
    match_arches = fields.List(fields.Str(), data_key='matchArches')
    match_releases = fields.List(fields.Str(), data_key='matchReleases')
    match_vendors = fields.List(fields.Str(), data_key='matchVendors')
    upload_group = fields.Str(data_key='uploadGroup')

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigMatch:
        return ImageConfigMatch(**data)


@dataclasses.dataclass
class ImageConfigArch:
    name: str
    azure_name: typing.Optional[str] = dataclasses.field(default=None)
    oci_arch: typing.Optional[str] = dataclasses.field(default=None)
    fai_classes: list[str] = dataclasses.field(default_factory=list)


class v1alpha1_ImageConfigArchSchema(Schema):
    name = fields.Str(required=True)
    azure_name = fields.Str(data_key='azureName')
    oci_arch = fields.Str(data_key='ociArch')
    fai_classes = fields.List(fields.Str(), data_key='faiClasses')

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigArch:
        return ImageConfigArch(**data)


@dataclasses.dataclass
class ImageConfigRelease:
    name: str
    basename: str
    id: str
    baseid: str
    fai_classes: list[str] = dataclasses.field(default_factory=list)
    matches: list[ImageConfigMatch] = dataclasses.field(default_factory=list)


class v1alpha1_ImageConfigReleaseSchema(Schema):
    name = fields.Str(required=True)
    basename = fields.Str(required=True)
    id = fields.Str(required=True)
    baseid = fields.Str(required=True)
    fai_classes = fields.List(fields.Str(), data_key='faiClasses')
    matches = fields.Nested(v1alpha1_ImageConfigMatchSchema, many=True)

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigRelease:
        return ImageConfigRelease(**data)


@dataclasses.dataclass
class ImageConfigType:
    name: str
    output_name: str
    output_version: str
    output_version_azure: str
    fai_classes: list[str] = dataclasses.field(default_factory=list)


class v1alpha1_ImageConfigTypeSchema(Schema):
    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str(), data_key='faiClasses')
    output_name = fields.Str(required=True, data_key='outputName')
    output_version = fields.Str(required=True, data_key='outputVersion')
    output_version_azure = fields.Str(required=True, data_key='outputVersionAzure')

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigType:
        return ImageConfigType(**data)


@dataclasses.dataclass
class ImageConfigPublicType:
    name: str
    matches: list[ImageConfigMatch] = dataclasses.field(default_factory=list)


class v1alpha1_ImageConfigPublicTypeSchema(Schema):
    name = fields.Str(required=True)
    matches = fields.Nested(v1alpha1_ImageConfigMatchSchema, many=True)

    @post_load
    def load_obj(self, data: dict[str, typing.Any], **kw) -> ImageConfigPublicType:
        return ImageConfigPublicType(**data)


@dataclasses.dataclass
class ImageConfigVendor:
    name: str
    size: int
    fai_classes: list[str] = dataclasses.field(default_factory=list)
    matches: list[ImageConfigMatch] = dataclasses.field(default_factory=list)


class v1alpha1_ImageConfigVendorSchema(Schema):
    name = fields.Str(required=True)
    fai_classes = fields.List(fields.Str(), data_key='faiClasses')
    size = fields.Integer(required=True)
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
