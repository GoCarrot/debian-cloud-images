from collections.abc import Mapping
from marshmallow import EXCLUDE


class TypeMetaRegistry(Mapping):
    def __init__(self):
        self._model = {}
        self._typemeta = {}

    def __getitem__(self, key):
        return self._typemeta[key]

    def __iter__(self):
        return iter(self._typemeta)

    def __len__(self):
        return len(self._typemeta)

    def dump(self, obj):
        try:
            cls = self._model[obj.__class__]
        except KeyError:
            raise ValueError(f'Unable to find schema for class={obj.__class__}')
        return cls(context={'registry': self}).dump(obj)

    def load(self, value, **kw):
        from .meta import TypeMeta, v1_TypeMetaSchema

        base = v1_TypeMetaSchema().load(value, unknown=EXCLUDE)
        typemeta = TypeMeta(base['kind'], base['api_version'])
        try:
            cls = self._typemeta[typemeta]
        except KeyError:
            raise ValueError(f'Unable to find schema for kind={typemeta.kind} and apiVersion={typemeta.api_version}')
        return cls(context={'registry': self}).load(value, **kw)

    def register(self, schema):
        self._model[schema.__model__] = schema
        self._typemeta[schema.__typemeta__] = schema
        return schema


registry = TypeMetaRegistry()
