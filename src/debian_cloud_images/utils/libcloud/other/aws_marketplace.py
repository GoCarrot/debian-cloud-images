# SPDX-License-Identifier: GPL-2.0-or-later

import json
import logging
from libcloud.common.aws import SignedAWSConnection, AWSDriver
from libcloud.common.base import Response


class StartChangesetResponse(Response):
    def __init__(self, r):
        self.r = r


class MarketplaceDriver(AWSDriver):
    name = 'aws-marketplace'
    region_name = ''


class MarketplaceConnection(SignedAWSConnection):
    driver = MarketplaceDriver
    service_name = 'aws-marketplace'
    region_name = ''

    def __init__(self, access_key_id=None, secret_key=None, region="us-east-1", token=None, signature_version=4):
        self.token = token
        self.region_name = region
        host = f'catalog.marketplace.{region}.amazonaws.com'
        super(MarketplaceConnection, self).__init__(access_key_id, secret_key, host=host,
                                                    token=self.token, signature_version=signature_version)
        self.driver.region_name = self.region_name

    @property
    def region(self):
        return self.region_name

    def start_changeset(self, catalog="AWSMarketplace", changeset=[], intent='APPLY'):
        _data = {
            'Catalog': 'AWSMarketplace',
            'ChangeSet': changeset,
            'Intent': intent,
        }
        data = json.dumps(_data, cls=JSONSerializeChangeSet)
        logging.debug(f'Posting {data}')
        headers = {
            'Content-type': 'application/json',
        }
        return StartChangesetResponse(self.request(
            '/StartChangeSet',
            headers=headers,
            method='POST',
            data=data))


class Change:
    _details = ''

    def __init__(self, changetype, entity={}, details={}):
        self._changetype = changetype
        self._entity = entity
        self._details = details


SECURITY_GROUPS = [
    {
        "IpProtocol": "tcp",
        "FromPort": 22,
        "ToPort": 22,
        "IpRanges": [
            "0.0.0.0/0"
        ],
    },
]


class VersionUpdate(Change):

    def __init__(
            self,
            entity_id,
            ami_id,
            version_title,
            role_arn,
            arch,
            release_notes,
            usage,
            default_instance_type,
            username='admin',
            operating_system='DEBIAN',
            security_groups=SECURITY_GROUPS,
    ):
        super().__init__('AddDeliveryOptions')
        self._details = {
            "Version": {
                'VersionTitle': version_title,
                'ReleaseNotes': release_notes,
            },
            'DeliveryOptions': [
                {
                    'Details': {
                        "AmiDeliveryOptionDetails": {
                            "AmiSource": {
                                "AmiId": ami_id,
                                "AccessRoleArn": role_arn,
                                "UserName": username,
                                "OperatingSystemName": operating_system,
                                "OperatingSystemVersion": version_title,
                            },
                            "UsageInstructions": usage,
                            "RecommendedInstanceType": default_instance_type,
                            "SecurityGroups": security_groups,
                        },
                    },
                },
            ]
        }

        self._entity = {
            'Identifier': entity_id,
            'Type': 'AmiProduct@1.0',
        }

    @property
    def entity_id(self):
        return self._entity['Identifier']


class JSONSerializeChangeSet(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ChangeSet):
            return {
                'Catalog': 'AWSMarketplace',
                'ChangeSet': o.changes,
            }
        elif isinstance(o, Change):
            return {
                'ChangeType': o._changetype,
                'Entity': o._entity,
                'DetailsDocument': o._details,
            }
        return json.JSONEncoder.default(self, o)


class ChangeSet:

    def __init__(self, connection, changes=[]):
        self.connection = connection
        self.changes = changes

    def append(self, change):
        self.changes.append(change)

    def apply(self, validate_only=False, dry_run=True):
        if dry_run:
            logging.info(f'DRY RUN: ChangeSet:\n{json.dumps(self.changes, indent=2, cls=JSONSerializeChangeSet)}')
            return StartChangesetResponse("DRY RUN, API not called")
        if len(self.changes) == 0:
            msg = "Empty changeset given"
            logging.info(msg)
            return StartChangesetResponse(msg)
        if validate_only:
            intent = 'VALIDATE'
        else:
            intent = 'APPLY'
        return self.connection.start_changeset(
            catalog='AWSMarketplace',
            changeset=self.changes,
            intent=intent)


# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
