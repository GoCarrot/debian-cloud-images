from collections import namedtuple
from marshmallow import Schema, fields, pre_dump, post_dump, post_load, ValidationError, validates


TypeMeta = namedtuple('TypeMeta', ['kind', 'api_version'])


class v1_TypeMetaSchema(Schema):
    __model__ = TypeMeta
    __typemeta__ = None

    api_version = fields.Str(required=True, data_key='apiVersion')
    kind = fields.Str(required=True)

    @post_dump
    def dump_typemeta(self, data):
        if self.__typemeta__:
            data['apiVersion'] = self.__typemeta__.api_version
            data['kind'] = self.__typemeta__.kind
        return data

    @validates('api_version')
    def validate_api_version(self, data):
        if self.__typemeta__ and self.__typemeta__.api_version != data:
            raise ValidationError('Input is of wrong api version')

    @validates('kind')
    def validate_kind(self, data):
        if self.__typemeta__ and self.__typemeta__.kind != data:
            raise ValidationError('Input is of wrong kind')


list_typemeta = TypeMeta('List', 'v1')


class v1_ListSchema(v1_TypeMetaSchema):
    __typemeta__ = list_typemeta

    items = fields.List(fields.Dict())

    @pre_dump
    def dump_items(self, data):
        return {
            'api_version': self.__typemeta__.api_version,
            'kind': self.__typemeta__.kind,
            'items': data,
        }

    @post_load
    def load_items(self, data):
        return list(data['items'])
