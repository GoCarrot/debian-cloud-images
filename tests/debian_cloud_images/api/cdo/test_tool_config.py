# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from marshmallow.exceptions import ValidationError

from debian_cloud_images.api.cdo.tool_config import v1alpha1_ToolConfigSchema


class Test_v1alpha1_ToolConfigSchema:
    schema = v1alpha1_ToolConfigSchema()

    def test_empty(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'ToolConfig',
        }

        obj = self.schema.load(data)
        assert data == self.schema.dump(obj)

    def test_full(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'ToolConfig',
            'metadata': {
                'name': 'test',
                'uid': '00000000-0000-0000-0000-000000000000',
            },
            'azure': {
                'auth': {
                    'client': '00000000-0000-0000-0000-000000000000',
                    'secret': 'test',
                },
                'cloudpartner': {
                    'publisher': 'test',
                    'tenant': '00000000-0000-0000-0000-000000000000',
                },
                'image': {
                    'group': 'test',
                    'subscription': '00000000-0000-0000-0000-000000000000',
                    'tenant': '00000000-0000-0000-0000-000000000000',
                },
                'storage': {
                    'group': 'test',
                    'name': 'test',
                    'subscription': '00000000-0000-0000-0000-000000000000',
                    'tenant': '00000000-0000-0000-0000-000000000000',
                },
            },
            'ec2': {
                'auth': {
                    'key': 'test',
                    'secret': 'test',
                },
                'storage': {
                    'name': 'test',
                },
                'image': {
                    'regions': ['all'],
                    'tags': ['Tag=Value'],
                },
                'marketplace': {
                    'role': 'dummy-arn',
                    'api_region': 'us-east-1',
                    'listings': {
                        'buster': {
                            'releasenotes': 'test url',
                            'entities': {
                                'arm64': {
                                    'id': 'arm64_entity_id',
                                    'instancetype': 't4g.medium',
                                },
                                'x86_64': {
                                    'id': 'x86_64_entity_id',
                                    'instancetype': 't3.medium',
                                },
                            },
                        },
                    },
                },
            },
            'gce': {
                'auth': {
                    'credentialsfile': 'test',
                },
                'image': {
                    'project': 'test',
                },
                'storage': {
                    'name': 'test',
                },
            },
        }

        obj = self.schema.load(data)
        assert obj['ec2']['marketplace']['api_region'] == 'us-east-1'
        assert obj['ec2']['marketplace']['listings']['buster']['entities']['arm64']['id'] == 'arm64_entity_id'
        assert data == self.schema.dump(obj)

    def test_unknown(self):
        data = {
            'apiVersion': 'cloud.debian.org/v1alpha1',
            'kind': 'ToolConfig',
            '__test': 'test',
        }

        with pytest.raises(ValidationError):
            self.schema.load(data)
