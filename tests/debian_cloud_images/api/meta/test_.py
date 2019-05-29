import pytest

from marshmallow import ValidationError

from debian_cloud_images.api.meta import TypeMeta, v1_TypeMetaSchema


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
