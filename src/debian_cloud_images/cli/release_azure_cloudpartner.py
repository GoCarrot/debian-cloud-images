import argparse
import logging
import sys

from libcloud.common.exceptions import BaseHTTPError

from .base import BaseCommand
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection


class AzureAuth:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret


class ActionAzureAuth(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, AzureAuth(*value.split(':')))


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
            action=ActionAzureAuth,
            help='Authentication info for Azure AD application',
            metavar='TENANT:APPLICATION:SECRET',
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
    parser = ReleaseAzureCloudpartnerCommand._argparse_init_base()
    args = parser.parse_args()
    ReleaseAzureCloudpartnerCommand(**vars(args))()
