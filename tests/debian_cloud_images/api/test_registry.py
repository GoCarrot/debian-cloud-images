from debian_cloud_images.api.meta import TypeMeta
from debian_cloud_images.api.registry import TypeMetaRegistry


class TestTypeMetaRegistry:
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
