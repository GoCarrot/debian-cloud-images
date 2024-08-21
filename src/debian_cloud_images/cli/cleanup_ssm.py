# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import logging

from .base import cli, BaseCommand
from ..utils.libcloud.compute.ec2 import ExEC2NodeDriver
from ..utils.libcloud.other.aws_ssm import SSMConnection


@cli.register(
    'cleanup-ssm',
    help='',
    epilog='''
config options:
  ec2.auth.key
  ec2.auth.secret
  ec2.image.regions
  ec2.ssm.prefix
''',
    arguments=[
        cli.prepare_argument(
            '--no-op',
            help="Dry run mode, don't actually do anything",
            action='store_true',
            dest='no_op',
        ),
        cli.prepare_argument(
            '--delete-after',
            help='Delete parameters older than X days',
            metavar='DAYS',
            type=int,
        ),
        cli.prepare_argument(
            '--max-deletions',
            help='Delete no more than this many variables',
            metavar='COUNT',
            dest='max_deletions',
            type=int,
        ),
        cli.prepare_argument(
            '--type',
            help='Clean up variables for the given release type (daily, release, etc)',
            type=str,
            dest='release_type',
            required=True,
        ),
        cli.prepare_argument(
            '--release',
            help="Handle the given release",
            dest='releases',
            metavar='NAME',
            default=[],
            action='append',
            required=True,
        ),
    ],
)
class CleanupSSMCommand(BaseCommand):
    compute_cls = ExEC2NodeDriver

    def __init__(
            self, *,
            delete_after=None,
            no_op=False,
            date_today=datetime.datetime.now(datetime.timezone.utc),
            max_deletions=50,
            release_type='daily',
            releases=[],
            **kw,
    ):
        super().__init__(**kw)
        self.no_op = no_op
        if delete_after:
            self.delete_date = date_today - datetime.timedelta(days=delete_after)
            logging.debug(f'Set delete_date to {self.delete_date}')
        else:
            self.delete_date = None
        self.ssm_prefix = self.config_get('ec2.ssm.prefix')
        self.access_key_id = self.config_get('ec2.auth.key')
        self.secret_key = self.config_get('ec2.auth.secret')
        self.token = self.config_get('ec2.auth.token', default=None)
        self.max_deletions = max_deletions
        regions = self.config_get('ec2.image.regions', default=["all"])
        self.release_type = release_type
        self.releases = releases

        if "all" in regions:
            # Figure out all the regions that EC2 knows about
            self.regions = [
                self.compute_cls(key=self.access_key_id, secret=self.secret_key,
                                 token=self.token, region=region.name)
                for region in self.compute_cls(key=self.access_key_id, secret=self.secret_key,
                                               token=self.token, region='us-east-1').ex_list_regions()
            ]
        else:
            self.regions = [self.compute_cls(key=self.access_key_id, secret=self.secret_key,
                                             token=self.token, region=region) for region in regions]

    def __call__(self):
        for region in self.regions:
            logging.debug(f'Running SSM parameter cleanup in {region}')
            c = SSMConnection(
                self.access_key_id,
                self.secret_key,
                region=region.region_name,
                token=self.token,
                signature_version=4,
            )

            for r in self.releases:
                self.handle_release(c, r)

    def handle_release(self, conn, release):
        path = '/'.join(
            (self.ssm_prefix, self.release_type, release)
        )
        logging.info(f'Deleting up to {self.max_deletions} variables from {path} in {conn.region}')
        results = conn.get_parameters_by_path(path, recursive=True,
                                              max_results=self.max_deletions)
        batch = []
        for j in results:
            if self.delete_date and j.last_modified < self.delete_date:
                logging.info(f'Deleting {j.name} -> {j.value} ({j.last_modified})')
                batch.append(j)
            else:
                logging.debug(f'Not deleting {j.name} ({j.last_modified})')
        if len(batch) > 0:
            conn.delete_parameters(batch, self.no_op)


# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
