import datetime
import logging

from .base import BaseCommand
from ..images.ec2 import Ec2Images
from ..utils.libcloud.compute.ec2 import ExEC2NodeDriver


class CleanupEc2Command(BaseCommand):
    argparser_name = 'cleanup-ec2'
    argparser_help = ''
    argparser_epilog = '''
config options:
  ec2.auth.key
  ec2.auth.secret
  ec2.image.regions
'''

    compute_cls = ExEC2NodeDriver

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--account',
            default='self',
            help='Delete images from account (default: %(default)s)',
            type=str,
        )
        parser.add_argument(
            '--delete-after',
            help='Delete images after X days',
            metavar='DAYS',
            type=int,
        )
        parser.add_argument(
            '--no-op',
            action='store_true',
        )

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

        self.drivers_compute = {
            region.name: self.compute_cls(key=key, secret=secret, token=token, region=region.name)
            for region in self.compute_cls(key=key, secret=secret, token=token, region='us-east-1').ex_list_regions()
        }

    def __call__(self):
        if self.delete_date:
            logging.info(f'Deleting images before {self.delete_date.strftime("%Y-%m-%d")}')
            Ec2Images(self.no_op, None, self.account, self.drivers_compute, None).cleanup(self.delete_date)
        else:
            logging.info('Not deleting images')


if __name__ == '__main__':
    CleanupEc2Command._main()
