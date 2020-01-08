import argparse
import logging
import sys

from libcloud.common.exceptions import BaseHTTPError

from .base import BaseCommand
from ..utils import argparse_ext
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


class ReleaseAzureCloudpartnerCommand(BaseCommand):
    argparser_name = 'release-azure-cloudpartner'
    argparser_help = 'release Debian images via Azure Cloud Partner interface'
    argparser_epilog = '''
config options:
  azure.cloudpartner.publisher
                       Azure publisher
'''

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--publisher',
            action=argparse_ext.HashItemAction,
            dest='config',
            dest_key='azure.cloudpartner.publisher',
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            '--offer',
            action='append',
            dest='offer_ids',
            help='Azure offer, can be specified multiple times',
            metavar='OFFER',
            required=True,
        )
        parser.add_argument(
            '--auth',
            action=argparse_ext.StoreAzureAuthAction,
        )

    def __init__(
            self, *,
            offer_ids=[],
            **kw,
    ):
        super().__init__(**kw)

        self.publisher_id = self.config_get('azure.cloudpartner.publisher', 'azure-publisher')
        self.offer_ids = offer_ids or []
        self.auth = self.config_get('azure-auth')

        self.__cloudpartner = None

    @property
    def cloudpartner(self):
        ret = self.__cloudpartner
        if ret is None:
            ret = AzureCloudpartnerOAuth2Connection(
                tenant_id=self.auth.tenant_id,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
            ret.connect()
            self.__cloudpartner = ret
        return ret

    def __call__(self):
        failed = False

        for offer_id in self.offer_ids:
            try:
                self.golive_offer(offer_id)
            except SystemExit:
                failed = True

        if failed:
            sys.exit(1)

    def golive_offer(self, offer_id):
        logging.info(f'Releasing offer {offer_id} of publisher {self.publisher_id}')
        try:
            self.cloudpartner.request(
                f'/api/publishers/{self.publisher_id}/offers/{offer_id}/golive',
                method='POST',
            )
        except BaseHTTPError as e:
            logging.error(f'Unable to release offer: {e.message}')
            sys.exit(1)


if __name__ == '__main__':
    ReleaseAzureCloudpartnerCommand._main()
