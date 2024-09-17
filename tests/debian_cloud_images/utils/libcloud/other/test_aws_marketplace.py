# SPDX-License-Identifier: GPL-2.0-or-later

import json
import pytest

from debian_cloud_images.utils.libcloud.other.aws_marketplace import (
    Change,
    ChangeSet,
    VersionUpdate,
    JSONSerializeChangeSet,
)


class TestAwsMarketplace:

    version_update = VersionUpdate('fake-entity-id',
                                   'ami-id-fake',
                                   '20240909-1234',
                                   'arn:dummy-arn:account-id:role',
                                   'arm64',
                                   'release notes',
                                   'usage text',
                                   't4g.ultra'
                                   )

    @pytest.fixture
    def mock_connection(self, monkeypatch):
        from unittest.mock import MagicMock
        return MagicMock()

    def test_versionupdate(self):
        assert self.version_update.entity_id == 'fake-entity-id'

    def test_dump_changeset(self, mock_connection):
        data = {
            'Catalog': 'AWSMarketplace',
            'ChangeSet': [
                {
                    "ChangeType": "AddDeliveryOptions",
                    "Entity": {
                        "Identifier": "example1-abcd-1234-5ef6-7890abcdef12@1",
                        "Type": "AmiProduct@1.0"
                    },
                    "DetailsDocument": {},
                },
            ],
        }
        cs = ChangeSet(mock_connection,
                       [
                           Change('AddDeliveryOptions',
                                  {
                                      "Identifier": "example1-abcd-1234-5ef6-7890abcdef12@1",
                                      "Type": "AmiProduct@1.0"
                                  },
                                  {}),
                       ],
                       )
        assert json.dumps(data) == json.dumps(cs, cls=JSONSerializeChangeSet)

    def test_changeset(self, mock_connection):
        c = ChangeSet(mock_connection)
        c.append(self.version_update)
        assert c.changes[0].entity_id == 'fake-entity-id'
        assert len(c.changes) == 1
        c.apply(dry_run=False)
        mock_connection.start_changeset.assert_called_once()


# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
