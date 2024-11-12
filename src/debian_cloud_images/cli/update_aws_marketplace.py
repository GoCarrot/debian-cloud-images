# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import pathlib

from .base import cli, BaseCommand
from ..images import Images
from ..utils.libcloud.other.aws_marketplace import MarketplaceConnection, ChangeSet, VersionUpdate


CONFIG_PREFIX = 'ec2.marketplace.listings'
USAGE_INSTRUCTIONS = """\
After launching your instance, connect to it using a Secure Shell (SSH) \
client with the SSH key you specified at launch. The default username is \
'admin'."""


class MarketplaceUpdater:

    def __init__(self, access_key_id, secret_key, token, changes, validate_only, dry_run, region='us-east-1'):
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.token = token
        self.validate_only = validate_only
        self.dry_run = dry_run
        self.region = region
        self.connection = MarketplaceConnection(access_key_id=access_key_id,
                                                secret_key=secret_key,
                                                token=token,
                                                region=region)
        self.changeset = ChangeSet(self.connection, changes)

    def add_change(self, change):
        self.changeset.append(change)

    def apply(self):
        self.changeset.apply(self.validate_only, self.dry_run)


@cli.register(
    'update-aws-marketplace',
    help='Update AWS Marketplace listings',
    epilog='''
config options:
  ec2.marketplace.role_arn    Role assumed by AWS services when access the given AMIs
  ec2.marketplace.api_region  Hosting region for the AWS Marketplace services [us-east-1]
  ec2.marketplace.listings    Map of release/architecture pairs to Marketplace entity IDs
''',
    arguments=[
        cli.prepare_argument(
            'manifests',
            help='read manifests',
            metavar='MANIFESTS',
            nargs='*',
            type=pathlib.Path,
        ),
        cli.prepare_argument(
            '--dry-run',
            help="Dry run mode, don't actually do anything",
            action='store_true',
            dest='dry_run',
        ),
        cli.prepare_argument(
            '--validate-only',
            help='Validate the change with AWS without applying',
            action='store_true',
            dest='validate_only',
        ),
    ],
)
class UpdateAwsMarketplaceCommand(BaseCommand):

    def _relnotes(self, release):
        return self.config_get('.'.join([CONFIG_PREFIX, release, 'releasenotes']), default="")

    def _default_instance_type(self, release, arch):
        return self.config_get('.'.join([CONFIG_PREFIX, release, 'entities', arch, 'instancetype']), default="")

    def _entity_id(self, release, arch):
        return self.config_get('.'.join([CONFIG_PREFIX, release, 'entities', arch, 'id']), default="")

    def _version_title(self, upload):
        release_name = upload.metadata.labels['debian.org/release']
        dist = upload.metadata.labels['debian.org/dist']
        arch = upload.metadata.labels['debian.org/arch']
        version = upload.metadata.labels['cloud.debian.org/version']
        releasemd = self.config_image.releases.get(release_name)
        release_id = releasemd.id
        return '-'.join([dist, release_id, arch, version])

    def extract_marketplace_uploads(self):
        """Extract the uploads relevant to a marketplace listing update from a set of manifests"""
        for name in self.images.keys():
            logging.debug(f'Processing {name}')
            for upload in self.images[name].uploads:
                if 'aws.amazon.com/region' in upload.metadata.labels:
                    if upload.metadata.labels['aws.amazon.com/region'] == self.api_region:
                        logging.debug('Found region')
                        entity_id = self._entity_id(upload.metadata.labels['debian.org/release'],
                                                    upload.metadata.labels['debian.org/arch'])
                        release_notes = self._relnotes(upload.metadata.labels['debian.org/release'])
                        instance_type = self._default_instance_type(upload.metadata.labels['debian.org/release'],
                                                                    upload.metadata.labels['debian.org/arch'])
                        version_title = self._version_title(upload)
                        usage = USAGE_INSTRUCTIONS
                        if entity_id != "":
                            logging.debug('Found AMI {} with entity_id {}'.format(
                                upload.ref,
                                entity_id))
                            c = VersionUpdate(
                                entity_id,
                                upload.ref,
                                version_title,
                                self.role_arn,
                                upload.metadata.labels['debian.org/arch'],
                                release_notes,
                                usage,
                                instance_type)
                            self.updater.add_change(c)

    def __init__(self, manifests=[], dry_run=False, validate_only=False, **kw):
        super().__init__(**kw)
        self.api_region = self.config_get('ec2.marketplace.api_region', default='us-east-1')
        self.role_arn = self.config_get('ec2.marketplace.role')
        self.validate_only = validate_only
        self.dry_run = dry_run
        self.updater = MarketplaceUpdater(
            access_key_id=self.config_get('ec2.auth.key'),
            secret_key=self.config_get('ec2.auth.secret'),
            token=self.config_get('ec2.auth.token', default=None),
            dry_run=dry_run,
            validate_only=validate_only,
            region=self.api_region,
            changes=[],
        )
        self.images = Images()
        for m in manifests:
            self.images.read(m)
        self.extract_marketplace_uploads()

    def __call__(self):
        self.updater.apply()

# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
