from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import tempfile
import typing
import yaml

from debian_cloud_images.images.azure_partnerlegacy.s1_offer import ImagesAzurePartnerlegacyOffer
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

from .base import BaseCommand


class ControlAzurePartnerlegacyCommand(BaseCommand):
    argparser_name = 'control-azure-partner'
    argparser_help = 'control various aspects of Azure Partner offers'
    argparser_epilog = '''
config options:
  azure.auth.client     application ID of service account, or empty for using az
  azure.auth.secret     secret of service account, or empty for using az
  azure.cloudpartner.tenant
  azure.cloudpartner.publisher
'''
    __argparser: argparse.ArgumentParser

    @classmethod
    def _argparse_register(cls, parser: argparse.ArgumentParser) -> None:
        super()._argparse_register(parser)

        cls.__argparser = parser
        parser.add_argument(
            '--partner-offer',
            help='use specified offer inside Azure Partner interface',
            metavar='OFFER',
            required=True,
        )
        parser.set_defaults(impl=None)

        subparsers = parser.add_subparsers(
            help='sub-command help',
        )
        parser_cat = subparsers.add_parser(
            name='cat',
            help='retrieve Azure Partner offer',
        )
        parser_cat.set_defaults(impl=cls.cat)
        parser_cat.add_argument(
            'slot',
            choices=['draft', 'preview', 'production'],
            help='retrieve specified slot (none (default), default, preview, production)',
            metavar='SLOT',
            nargs='?',
        )
        parser_edit = subparsers.add_parser(
            name='edit',
            help='edit Azure Partner offer',
        )
        parser_edit.set_defaults(impl=cls.edit)
        parser_golive = subparsers.add_parser(
            name='golive',
            help='perform Go Live operation on Azure Partner offer',
        )
        parser_golive.set_defaults(impl=cls.golive)
        parser_publish = subparsers.add_parser(
            name='publish',
            help='perform Publish operation on Azure Partner offer',
        )
        parser_publish.set_defaults(impl=cls.publish)

    def __init__(
            self, *,
            impl: typing.Callable[[ControlAzurePartnerlegacyCommand, ImagesAzurePartnerlegacyOffer], None],
            partner_offer: str,
            slot: str = None,
            **kw,
    ) -> None:
        super().__init__(**kw)

        self._impl = impl
        self._partner_offer = partner_offer
        self._slot = slot

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._partner_tenant = str(self.config_get('azure.cloudpartner.tenant'))
        self._partner_publisher = self.config_get('azure.cloudpartner.publisher')

        if impl is None:
            self.__argparser.print_help()
            self.__argparser.exit(2)

    def __call__(self) -> None:
        partner_conn = AzureGenericOAuth2Connection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._partner_tenant,
            subscription_id=None,
            host='cloudpartner.azure.com',
            login_resource='https://cloudpartner.azure.com',
        )

        partner_offer = ImagesAzurePartnerlegacyOffer(
            self._partner_publisher,
            self._partner_offer,
            partner_conn,
        )

        self._impl(self, partner_offer)

    def cat(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        data = partner_offer.get(slot=self._slot)
        with subprocess.Popen(['pager'], stdin=subprocess.PIPE) as p:
            p.communicate(yaml.safe_dump(data).encode('utf-8'))

    def edit(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        data = partner_offer.get()

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            yaml.safe_dump(data, f)
            f.flush()
            subprocess.check_call(['editor', f.name])
            f.seek(0)
            data_changed = yaml.safe_load(f)

        diff = list(difflib.unified_diff(
            json.dumps(data, sort_keys=True, indent=4).split('\n'),
            json.dumps(data_changed, sort_keys=True, indent=4).split('\n'),
            'Original',
            'New',
        ))

        if diff:
            for line in diff:
                print(line.rstrip())

            print()
            accept = input('Commit? (y)')
            if accept == 'y':
                partner_offer.put(data_changed)
            else:
                print('Not committing')

        else:
            print('No changes')

    def golive(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        partner_offer.control_golive()
        print(f'Executed Go Live operation on: {self._partner_publisher}/{self._partner_offer}')

    def publish(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        partner_offer.control_publish()
        print(f'Executed Publish operation on: {self._partner_publisher}/{self._partner_offer}')


if __name__ == '__main__':
    ControlAzurePartnerlegacyCommand._main()
