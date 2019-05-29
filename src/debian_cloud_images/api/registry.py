from collections.abc import Mapping


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

    def register(self, schema):
        self._model[schema.__model__] = schema
        self._typemeta[schema.__typemeta__] = schema
        return schema


registry = TypeMetaRegistry()
