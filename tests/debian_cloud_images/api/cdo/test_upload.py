# SPDX-License-Identifier: GPL-2.0-or-later

from debian_cloud_images.api.cdo.upload import v1alpha1_UploadSchema


class Test_v1alpha1_UploadSchema:
    schema = v1alpha1_UploadSchema()

    def test(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'Upload',
            'metadata': {
                'uid': '00000000-0000-0000-0000-000000000000',
            },
            'data': {
                'familyRef': 'ref',
                'provider': 'example.com',
                'ref': 'ref',
            },
        }

        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)
