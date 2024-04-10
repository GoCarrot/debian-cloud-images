# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import logging

from .base import cli, BaseCommand
from ..images.ec2 import Ec2Images
from ..utils.libcloud.compute.ec2 import ExEC2NodeDriver


@cli.register(
    'cleanup-ec2',
    help='',
    epilog='''
config options:
  ec2.auth.key
  ec2.auth.secret
  ec2.image.regions
''',
    arguments=[
        cli.prepare_argument(
            '--account',
            default='self',
            help='Delete images from account (default: %(default)s)',
            type=str,
        ),
        cli.prepare_argument(
            '--delete-after',
            help='Delete images after X days',
            metavar='DAYS',
            type=int,
        ),
        cli.prepare_argument(
            '--no-op',
            action='store_true',
        ),
    ],
)
class CleanupEc2Command(BaseCommand):
    compute_cls = ExEC2NodeDriver

    def __init__(
            self, *,
            account=None,
            delete_after=None,
            no_op=False,
            date_today=datetime.datetime.now(),
            **kw,
    ):
        super().__init__(**kw)
        self.no_op = no_op
        self.account = account

        if delete_after:
            self.delete_date = date_today - datetime.timedelta(days=delete_after)
        else:
            self.delete_date = None

        key = self.config_get('ec2.auth.key')
        secret = self.config_get('ec2.auth.secret')
        token = self.config_get('ec2.auth.token', default=None)
        regions = self.config_get('ec2.image.regions', default=["all"])

        if "all" in regions:
            self.drivers_compute = {
                region.name: self.compute_cls(key=key, secret=secret, token=token, region=region.name)
                for region in self.compute_cls(key=key, secret=secret, token=token, region='us-east-1').ex_list_regions()
            }
        else:
            self.drivers_compute = {
                region: self.compute_cls(key=key, secret=secret, token=token, region=region)
                for region in regions
            }

    def __call__(self):
        if self.delete_date:
            logging.info(f'Deleting images before {self.delete_date.strftime("%Y-%m-%d")}')
            Ec2Images(self.no_op, None, self.account, self.drivers_compute, None).cleanup(self.delete_date)
        else:
            logging.info('Not deleting images')


if __name__ == '__main__':
    cli.main(CleanupEc2Command)
