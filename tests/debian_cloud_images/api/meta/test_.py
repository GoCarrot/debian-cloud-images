# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

import copy

from marshmallow import post_load, ValidationError

from debian_cloud_images.api.meta import TypeMeta, v1_ListSchema, v1_ObjectMetaSchema, v1_TypeMetaSchema
from debian_cloud_images.api.registry import registry as api_registry


class Test_v1_ListSchema:
    schema = v1_ListSchema()

    def test_no_items(self):
        data = {
            'apiVersion': 'v1',
            'kind': 'List',
        }

        obj = self.schema.load(data)

        assert isinstance(obj, list)
        assert len(obj) == 0

        assert data == self.schema.dump(obj)

    def test_items(self):
        registry = copy.deepcopy(api_registry)

        class TestOne:
            pass

        @registry.register
        class TestOneSchema(v1_TypeMetaSchema):
            __model__ = TestOne
            __typemeta__ = TypeMeta('One', 'v1')

            @post_load
            def load_obj(self, data, **kw):
                return self.__model__()

        data = {
            'apiVersion': 'v1',
            'kind': 'List',
            'items': [
                {
                    'apiVersion': 'v1',
                    'kind': 'One',
                },
            ],
        }

        obj = registry.load(data)

        assert isinstance(obj, list)
        assert len(obj) == 1

        assert data == registry.dump(obj)


class Test_v1_ObjectMetaSchema:
    schema = v1_ObjectMetaSchema()

    def test_annotations(self):
        data = {
            'annotations': {
                'test': 'test',
            },
            'uid': '00000000-0000-0000-0000-000000000000',
        }
        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)

    def test_name(self):
        data = {
            'name': 'name',
            'uid': '00000000-0000-0000-0000-000000000000',
        }
        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)

    def test_labels(self):
        data = {
            'labels': {
                'test': 'test',
            },
            'uid': '00000000-0000-0000-0000-000000000000',
        }
        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)

    def test_uid(self):
        data = {
            'uid': '00000000-0000-0000-0000-000000000000',
        }
        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)


class Test_v1_TypeMetaSchema:
    class Schema(v1_TypeMetaSchema):
        __typemeta__ = TypeMeta('Test', 'test/v1')

    schema = Schema()

    def test_correct(self):
        data = {
            'apiVersion': 'test/v1',
            'kind': 'Test',
        }

        valid_data = self.schema.load(data)

        assert data == self.schema.dump(valid_data)

    def test_wrong_api_version(self):
        data = {
            'apiVersion': 'wrong/v1',
            'kind': 'Test',
        }

        with pytest.raises(ValidationError) as exc_info:
            self.schema.load(data)

        assert exc_info.value.messages.get('apiVersion')

    def test_wrong_kind(self):
        data = {
            'apiVersion': 'test/v1',
            'kind': 'Wrong',
        }

        with pytest.raises(ValidationError) as exc_info:
            self.schema.load(data)

        assert exc_info.value.messages.get('kind')
