# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.api.meta import TypeMeta, v1_TypeMetaSchema
from debian_cloud_images.api.registry import TypeMetaRegistry


class TestTypeMetaRegistry:
    def test_dump(self):
        registry = TypeMetaRegistry()

        class TestOne:
            pass

        @registry.register
        class TestOneSchema(v1_TypeMetaSchema):
            __model__ = TestOne
            __typemeta__ = TypeMeta('One', 'v1')

        data = {
            'apiVersion': 'v1',
            'kind': 'One',
        }

        assert registry.dump(TestOne()) == data

    def test_dump_unknown(self):
        registry = TypeMetaRegistry()

        with pytest.raises(ValueError):
            registry.dump(object())

    def test_load(self):
        registry = TypeMetaRegistry()

        @registry.register
        class TestOneSchema(v1_TypeMetaSchema):
            __typemeta__ = TypeMeta('One', 'v1')

        data = {
            'apiVersion': 'v1',
            'kind': 'One',
        }

        registry.load(data)

    def test_load_default(self):
        registry = TypeMetaRegistry()

        @registry.register
        class TestOneSchema(v1_TypeMetaSchema):
            __typemeta__ = TypeMeta('One', 'v1')

        data = {}

        registry.load(data, default_typemeta=TestOneSchema.__typemeta__)

    def test_load_empty(self):
        registry = TypeMetaRegistry()

        @registry.register
        class TestOneSchema(v1_TypeMetaSchema):
            __typemeta__ = TypeMeta('One', 'v1')

        data = {}

        with pytest.raises(ValueError):
            registry.load(data)

    def test_load_unknown(self):
        registry = TypeMetaRegistry()

        data = {
            'apiVersion': 'v1',
            'kind': 'One',
        }

        with pytest.raises(ValueError):
            registry.load(data)

    def test_register(self):
        registry = TypeMetaRegistry()

        typemeta_1 = TypeMeta('One', 'v1')
        typemeta_2 = TypeMeta('Two', 'v1')
        typemeta_2_1 = TypeMeta('Two', 'v1')

        class TestOne:
            __model__ = object()
            __typemeta__ = typemeta_1

        class TestTwo:
            __model__ = object()
            __typemeta__ = typemeta_2

        registry.register(TestOne)
        registry.register(TestTwo)

        assert registry[typemeta_1] is TestOne
        assert registry[typemeta_2] is TestTwo
        assert registry[typemeta_2_1] is TestTwo
