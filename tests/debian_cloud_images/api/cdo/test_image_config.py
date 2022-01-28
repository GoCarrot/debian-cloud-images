import pytest

from marshmallow.exceptions import ValidationError

from debian_cloud_images.api.cdo.image_config import v1alpha1_ImageConfigSchema


class Test_v1alpha1_ImageConfigSchema:
    schema = v1alpha1_ImageConfigSchema()

    def test_empty(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'ImageConfig',
        }

        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)

    def test_unknown(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'ImageConfig',
            '__test': 'test',
        }

        with pytest.raises(ValidationError):
            self.schema.load(data)
