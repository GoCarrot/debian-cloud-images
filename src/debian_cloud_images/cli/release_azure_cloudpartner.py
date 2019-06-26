import logging
import sys

from libcloud.common.exceptions import BaseHTTPError

from .base import BaseCommand
from ..utils import argparse_ext
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


class ReleaseAzureCloudpartnerCommand(BaseCommand):
    argparser_name = 'release-azure-cloudpartner'
    argparser_help = 'release Debian images via Azure Cloud Partner interface'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--publisher',
            dest='publisher_id',
            help='Azure publisher',
            metavar='PUBLISHER',
            required=True,
        )
        parser.add_argument(
            '--offer',
            dest='offer_id',
            help='Azure offer',
            metavar='OFFER',
            required=True,
        )
        parser.add_argument(
            '--auth',
            action=argparse_ext.ActionAzureAuth,
            required=True,
        )

    def __init__(
            self, *,
            publisher_id,
            offer_id,
            auth=None,
            **kw,
    ):
        super().__init__(**kw)

        self.publisher_id = publisher_id
        self.offer_id = offer_id
        self.auth = auth

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
        try:
            logging.info(f'Releasing {self.publisher_id}:{self.offer_id}')
            self.cloudpartner.request(
                f'/api/publishers/{self.publisher_id}/offers/{self.offer_id}/golive',
                method='POST',
            )
        except BaseHTTPError as e:
            logging.error(f'Unable to release offer: {e.message}')
            sys.exit(1)


if __name__ == '__main__':
    ReleaseAzureCloudpartnerCommand._main()
