# SPDX-License-Identifier: GPL-2.0-or-later

import json
import pytest

from unittest.mock import MagicMock

from debian_cloud_images.cli.update_aws_marketplace import UpdateAwsMarketplaceCommand
from debian_cloud_images.utils.libcloud.other.aws_marketplace import MarketplaceConnection


@pytest.fixture
def images_path(tmp_path):
    with tmp_path.joinpath("test-nomatch.json").open('w') as f:
        json.dump({
            'apiVersion': 'v1',
            'items': [
                {
                    'apiVersion': 'cloud.debian.org/v1alpha1',
                    'kind': 'Upload',
                    'metadata': {
                        'uid': '00000000-0000-0000-0000-000000000001',
                        'labels': {
                            'aws.amazon.com/region': 'eu-north-1',
                            'cloud.debian.org/vendor': 'ec2',
                            'cloud.debian.org/version': '20240904-1860',
                            'debian.org/arch': 'arm64',
                            'debian.org/dist': 'debian',
                            'debian.org/release': 'bullseye',
                            'upload.cloud.debian.org/provider': 'aws.amazon.com',
                            'upload.cloud.debian.org/type': 'release'
                        },
                    },
                    'data': {
                        'familyRef': None,
                        'provider': 'ec2.eu-west-3.amazonaws.com',
                        'ref': 'ami-095fb177917870fc0'
                    },
                },
                {
                    "apiVersion": "cloud.debian.org/v1alpha1",
                    "data": {
                        "familyRef": None,
                        "provider": "ec2.us-east-1.amazonaws.com",
                        "ref": "ami-00a66714870c8a94b"
                    },
                    "kind": "Upload",
                    "metadata": {
                        "labels": {
                            "aws.amazon.com/region": "ap-northeast-1",
                            "cloud.debian.org/vendor": "ec2",
                            "cloud.debian.org/version": "20240904-1860",
                            "debian.org/arch": "arm64",
                            "debian.org/dist": "debian",
                            "debian.org/release": "bullseye",
                            "upload.cloud.debian.org/provider": "aws.amazon.com",
                            "upload.cloud.debian.org/type": "release"
                        },
                        "uid": "7275cded-42fc-4313-8882-8481fd6ea8cd"
                    }
                },
            ],
            "kind": "List",
        }, f)

    with tmp_path.joinpath("test.upload.json").open('w') as f:
        json.dump({
            'apiVersion': 'v1',
            'items': [
                {
                    'apiVersion': 'cloud.debian.org/v1alpha1',
                    'kind': 'Upload',
                    'metadata': {
                        'uid': '00000000-0000-0000-0000-000000000001',
                        'labels': {
                            'aws.amazon.com/region': 'eu-north-1',
                            'cloud.debian.org/vendor': 'ec2',
                            'cloud.debian.org/version': '20240904-1860',
                            'debian.org/arch': 'arm64',
                            'debian.org/dist': 'debian',
                            'debian.org/release': 'bullseye',
                            'upload.cloud.debian.org/provider': 'aws.amazon.com',
                            'upload.cloud.debian.org/type': 'release'
                        },
                    },
                    'data': {
                        'familyRef': None,
                        'provider': 'ec2.eu-west-3.amazonaws.com',
                        'ref': 'ami-095fb177917870fc0'
                    },
                },
                {
                    "apiVersion": "cloud.debian.org/v1alpha1",
                    "data": {
                        "familyRef": None,
                        "provider": "ec2.us-east-1.amazonaws.com",
                        "ref": "ami-00a66714870c8a94b"
                    },
                    "kind": "Upload",
                    "metadata": {
                        "labels": {
                            "aws.amazon.com/region": "us-east-1",
                            "cloud.debian.org/vendor": "ec2",
                            "cloud.debian.org/version": "20240904-1860",
                            "debian.org/arch": "arm64",
                            "debian.org/dist": "debian",
                            "debian.org/release": "bullseye",
                            "upload.cloud.debian.org/provider": "aws.amazon.com",
                            "upload.cloud.debian.org/type": "release"
                        },
                        "uid": "7275cded-42fc-4313-8882-8481fd6ea8cd"
                    }
                },
            ],
            "kind": "List",
        }, f)

        with tmp_path.joinpath("test.upload.2.json").open('w') as f:
            json.dump({
                'apiVersion': 'v1',
                'items': [
                    {
                        "apiVersion": "cloud.debian.org/v1alpha1",
                        "data": {
                            "familyRef": None,
                            "provider": "ec2.us-east-1.amazonaws.com",
                            "ref": "ami-00000000000000001"
                        },
                        "kind": "Upload",
                        "metadata": {
                            "labels": {
                                "aws.amazon.com/region": "us-east-1",
                                "cloud.debian.org/vendor": "ec2",
                                "cloud.debian.org/version": "20240904-1860",
                                "debian.org/arch": "amd64",
                                "debian.org/dist": "debian",
                                "debian.org/release": "bullseye",
                                "upload.cloud.debian.org/provider": "aws.amazon.com",
                                "upload.cloud.debian.org/type": "release"
                            },
                            "uid": "00000000-0000-0000-0000-000000000001"
                        }
                    },
                ],
                "kind": "List",
            }, f)

    return tmp_path


class TestAwsMarketplaceAutomation:
    region = 'us-east-1'
    arch = 'arm64'

    config = {
        'ec2.marketplace.role': 'arn:xyz-tesing:acct:role',
        'ec2.auth.key': 'test-key',
        'ec2.auth.secret': 'test-secret',
        'ec2.marketplace.listings.bullseye.entities.arm64.id': 'test-bullseye-arm64-entity',
        'ec2.marketplace.listings.bullseye.releasenotes': 'URL',
        'ec2.marketplace.listings.bullseye.entities.arm64.instancetype': 't4g.ultra',
        'ec2.marketplace.listings.bullseye.entities.amd64.id': 'test-bullseye-amd64-entity',
        'ec2.marketplace.listings.bullseye.entities.amd64.instancetype': 't3.pico',
    }

    # Execution with an empty configuration shouldn't result in any
    # populated changesets or API calls, but also should not crash
    def test_unconfigured(self, monkeypatch, images_path):
        mock_updater = MagicMock()
        monkeypatch.setattr(MarketplaceConnection, 'start_changeset', mock_updater)
        manifests = [images_path / 'test.upload.json']
        c = UpdateAwsMarketplaceCommand(manifests, dry_run=False, config={})
        c()
        assert len(c.updater.changeset.changes) == 0
        mock_updater.assert_not_called()

    # A change is posted to the service
    def test_full(self, monkeypatch, images_path):
        mock_updater = MagicMock()
        monkeypatch.setattr(MarketplaceConnection, 'start_changeset', mock_updater)
        manifests = [images_path / 'test.upload.json']
        c = UpdateAwsMarketplaceCommand(manifests, dry_run=False, config=self.config)
        c()
        assert len(c.updater.changeset.changes) == 1
        mock_updater.assert_called_once()

    def test_multiple(self, monkeypatch, images_path):
        mock_updater = MagicMock()
        monkeypatch.setattr(MarketplaceConnection, 'start_changeset', mock_updater)
        manifests = [images_path / 'test.upload.json', images_path / 'test.upload.2.json']
        c = UpdateAwsMarketplaceCommand(manifests, dry_run=False, config=self.config)
        c()
        assert len(c.updater.changeset.changes) == 2
        mock_updater.assert_called_once()

    # A manifest contains uploads, but none of appropriate for our configuration.
    # This should result in an empty changeset and no API calls
    def test_nomatch(self, monkeypatch, images_path):
        mock_updater = MagicMock()
        monkeypatch.setattr(MarketplaceConnection, 'start_changeset', mock_updater)
        manifests = [images_path / 'test-nomatch.json']
        c = UpdateAwsMarketplaceCommand(manifests, dry_run=False, config=self.config)
        c()
        assert len(c.updater.changeset.changes) == 0
        mock_updater.assert_not_called()

    def test_release_notes_env(self, monkeypatch, images_path):
        mock_updater = MagicMock()
        monkeypatch.setattr(MarketplaceConnection, 'start_changeset', mock_updater)
        value = 'release notes test value'
        monkeypatch.setenv('DCI_CONFIG_ec2_marketplace_listings_bullseye_releasenotes', value)
        manifests = [images_path / 'test.upload.json']
        c = UpdateAwsMarketplaceCommand(manifests, dry_run=True, config=self.config)
        c()
        assert len(c.updater.changeset.changes) == 1
        assert value in str(c.updater.changeset.changes[0]._details)


# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
