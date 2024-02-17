# SPDX-License-Identifier: GPL-2.0-or-later

from debian_cloud_images.api.cdo.build import v1alpha1_BuildSchema


class Test_v1alpha1_BuildSchema:
    schema = v1alpha1_BuildSchema()

    def test(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'Build',
            'metadata': {
                'uid': '00000000-0000-0000-0000-000000000000',
            },
            'data': {
                'info': {},
                'packages': [
                    {'name': 'foo', 'version': 'v0'},
                    {'name': 'bar', 'version': 'v1'},
                ],
            },
        }

        obj = self.schema.load(data)

        assert len(obj.packages) == 2
        assert obj.packages[0]['version'] == 'v0'
        assert obj.packages[1]['version'] == 'v1'

        assert data == self.schema.dump(obj)
