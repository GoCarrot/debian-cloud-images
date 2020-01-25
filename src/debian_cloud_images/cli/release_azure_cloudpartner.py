import logging
import sys

from collections import namedtuple
from libcloud.common.exceptions import BaseHTTPError

from .base import BaseCommand
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


AzureAuth = namedtuple('AzureAuth', ('client', 'secret'))
AzureCloudpartner = namedtuple('AzureCloudpartner', ('tenant', 'publisher'))


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
            '--offer',
            action='append',
            dest='offer_ids',
            help='Azure offer, can be specified multiple times',
            metavar='OFFER',
            required=True,
        )

    def __init__(
            self, *,
            offer_ids=[],
            **kw,
    ):
        super().__init__(**kw)

        self.auth = AzureAuth(
            client=str(self.config_get('azure.auth.client')),
            secret=self.config_get('azure.auth.secret'),
        )
        self.cloudpartner = AzureCloudpartner(
            tenant=str(self.config_get('azure.cloudpartner.tenant')),
            publisher=self.config_get('azure.cloudpartner.publisher'),
        )
        self.offer_ids = offer_ids or []

        self.__cloudpartner_obj = None

    @property
    def cloudpartner_obj(self):
        ret = self.__cloudpartner_obj
        if ret is None:
            ret = AzureCloudpartnerOAuth2Connection(
                tenant_id=self.cloudpartner.tenant,
                client_id=self.auth.client,
                client_secret=self.auth.secret,
            )
            ret.connect()
            self.__cloudpartner_obj = ret
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
        logging.info(f'Releasing offer {offer_id} of publisher {self.cloudpartner.publisher}')
        try:
            self.cloudpartner_obj.request(
                f'/api/publishers/{self.cloudpartner.publisher}/offers/{offer_id}/golive',
                method='POST',
            )
        except BaseHTTPError as e:
            logging.error(f'Unable to release offer: {e.message}')
            sys.exit(1)


if __name__ == '__main__':
    ReleaseAzureCloudpartnerCommand._main()
