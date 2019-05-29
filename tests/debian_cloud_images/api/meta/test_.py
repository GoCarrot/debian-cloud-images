import pytest

from marshmallow import ValidationError

from debian_cloud_images.api.meta import TypeMeta, v1_ListSchema, v1_ObjectMetaSchema, v1_TypeMetaSchema


class Test_v1_ListSchema:
    schema = v1_ListSchema()

    def test_no_items(self):
        data = {
            'apiVersion': 'v1',
            'kind': 'List',
            'items': [],
        }

        obj = self.schema.load(data)

        assert isinstance(obj, list)
        assert len(obj) == 0

        assert data == self.schema.dump(obj)

    def test_items(self):
        data = {
            'apiVersion': 'v1',
            'kind': 'List',
            'items': [
                {
                    'apiVersion': 'unknown/v1',
                    'kind': 'Unknown',
                },
            ],
        }

        obj = self.schema.load(data)

        assert isinstance(obj, list)
        assert len(obj) == 1

        assert data == self.schema.dump(obj)


class Test_v1_ObjectMetaSchema:
    schema = v1_ObjectMetaSchema()

    def test(self):
        data = {
            'labels': {
                'test': 'test',
            },
            'uid': '00000000-0000-0000-0000-000000000000',
        }

        obj = self.schema.load(data)

        assert data == self.schema.dump(obj)


class Test_v1_TypeMetaSchema:
    class TestSchema(v1_TypeMetaSchema):
        __typemeta__ = TypeMeta('Test', 'test/v1')

    schema = TestSchema()

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
