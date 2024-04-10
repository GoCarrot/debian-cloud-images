# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import logging
import pathlib

from .base import cli, BaseCommand
from ..images.public import PublicImages
from ..images.publicinfo import ImagePublicType
from ..utils import argparse_ext


@cli.register(
    'cleanup',
    help='',
    arguments=[
        cli.prepare_argument(
            '--release',
            action='append',
            default=[],
            dest='releases',
            help='Delete images from release',
            required=True,
        ),
        cli.prepare_argument(
            '--storage',
            help='base path for storage',
            metavar='PATH',
            required=True,
            type=pathlib.Path,
        ),
        cli.prepare_argument(
            '--delete-after',
            help='Delete images after X days',
            metavar='DAYS',
            type=int,
        ),
        cli.prepare_argument(
            '--public-type',
            action=argparse_ext.ActionEnum,
            default='dev',
            dest='public_type',
            enum=ImagePublicType,
            metavar='TYPE',
        ),
        cli.prepare_argument(
            '--no-op',
            action='store_true',
        ),
    ],
)
class CleanupCommand(BaseCommand):
    def __init__(
            self, *,
            releases=[],
            storage=None,
            delete_after=None,
            public_type=None,
            no_op=False,
            date_today=datetime.datetime.now(),
            **kw,
    ):
        super().__init__(**kw)
        self.releases = releases
        self.storage = storage
        self.public_type = public_type
        self.no_op = no_op

        if delete_after is not None:
            self.delete_date = date_today - datetime.timedelta(days=delete_after)
        else:
            self.delete_date = None

    def __call__(self):
        if self.delete_date:
            logging.info(f'Deleting images before {self.delete_date.strftime("%Y-%m-%d")}')
            PublicImages(
                self.no_op,
                None,
                self.public_type.name,
                self.storage,
                None,
            ).cleanup(self.delete_date, self.releases)
        else:
            logging.info('Not deleting images')


if __name__ == '__main__':
    cli.main(CleanupCommand)
