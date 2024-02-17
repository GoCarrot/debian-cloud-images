# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import typing

from collections.abc import Mapping
from marshmallow import EXCLUDE

from . import meta


class TypeMetaRegistry(Mapping):
    _model: dict[typing.Type, typing.Type[meta.v1_TypeMetaSchema]]
    _typemeta: dict[meta.TypeMeta, typing.Type[meta.v1_TypeMetaSchema]]

    def __init__(self) -> None:
        self._model = {}
        self._typemeta = {}

    def __getitem__(self, key: meta.TypeMeta) -> typing.Type[meta.v1_TypeMetaSchema]:
        return self._typemeta[key]

    def __iter__(self) -> typing.Iterator[meta.TypeMeta]:
        return iter(self._typemeta)

    def __len__(self) -> int:
        return len(self._typemeta)

    def dump(self, obj: object) -> object:
        try:
            cls = self._model[obj.__class__]
        except KeyError:
            raise ValueError(f'Unable to find schema for class={obj.__class__}')
        return cls(context={'registry': self}).dump(obj)

    def load(
            self,
            value: typing.Mapping[str, typing.Any],
            default_typemeta: typing.Optional[meta.TypeMeta] = None,
            **kw,
    ) -> object:
        base = meta.v1_TypeMetaSchema().load(value, unknown=EXCLUDE)
        typemeta = meta.TypeMeta(
            base.get('kind', default_typemeta and default_typemeta.kind),
            base.get('api_version', default_typemeta and default_typemeta.api_version),
        )

        try:
            cls = self._typemeta[typemeta]
        except KeyError:
            raise ValueError(f'Unable to find schema for kind={typemeta.kind} and apiVersion={typemeta.api_version}')
        return cls(context={'registry': self}).load(value, **kw)

    def register(self, schema: typing.Type[meta.v1_TypeMetaSchema]) -> typing.Type[meta.v1_TypeMetaSchema]:
        assert schema.__typemeta__ is not None
        self._model[schema.__model__] = schema
        self._typemeta[schema.__typemeta__] = schema
        return schema


registry = TypeMetaRegistry()
