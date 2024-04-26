# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import difflib
import json
import subprocess
import tempfile
import yaml

from debian_cloud_images.images.azure_partnerlegacy.s1_offer import ImagesAzurePartnerlegacyOffer
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection

from .base import cli, BaseCommand
from typing import Optional


cli_command = cli.register_subparsers(
    'control-azure-partner',
    help='control various aspects of Azure Partner offers',
    epilog='''
    config options:
      azure.auth.client     application ID of service account, or empty for using az
      azure.auth.secret     secret of service account, or empty for using az
      azure.cloudpartner.tenant
      azure.cloudpartner.publisher
    ''',
    arguments=[
        cli.prepare_argument(
            '--partner-offer',
            help='use specified offer inside Azure Partner interface',
            metavar='OFFER',
            required=True,
        ),
    ],
)


class ControlAzurePartnerlegacyCommand(BaseCommand):
    def __init__(
            self, *,
            partner_offer: str,
            slot: Optional[str] = None,
            **kw,
    ) -> None:
        super().__init__(**kw)

        self._partner_offer = partner_offer
        self._slot = slot

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._partner_tenant = str(self.config_get('azure.cloudpartner.tenant'))
        self._partner_publisher = self.config_get('azure.cloudpartner.publisher')

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

        self.impl(partner_offer)

    def impl(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        raise NotImplementedError


@cli_command.register(
    'cat',
    help='retrieve Azure Partner offer',
    arguments=[
        cli_command.prepare_argument(
            'slot',
            choices=['draft', 'preview', 'production'],
            help='retrieve specified slot (none (default), default, preview, production)',
            metavar='SLOT',
            nargs='?',
        ),
    ],
)
class ControlAzurePartnerlegacyCommandCat(ControlAzurePartnerlegacyCommand):
    def impl(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        data = partner_offer.get(slot=self._slot)
        with subprocess.Popen(['sensible-pager'], stdin=subprocess.PIPE) as p:
            p.communicate(yaml.safe_dump(data).encode('utf-8'))


@cli_command.register(
    'edit',
    help='edit Azure Partner offer',
)
class ControlAzurePartnerlegacyCommandEdit(ControlAzurePartnerlegacyCommand):
    def impl(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
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


@cli_command.register(
    'golive',
    help='perform Go Live operation on Azure Partner offer',
)
class ControlAzurePartnerlegacyCommandGoline(ControlAzurePartnerlegacyCommand):
    def impl(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        partner_offer.control_golive()
        print(f'Executed Go Live operation on: {self._partner_publisher}/{self._partner_offer}')


@cli_command.register(
    'publish',
    help='perform Publish operation on Azure Partner offer',
)
class ControlAzurePartnerlegacyCommandPublish(ControlAzurePartnerlegacyCommand):
    def impl(self, partner_offer: ImagesAzurePartnerlegacyOffer) -> None:
        partner_offer.control_publish()
        print(f'Executed Publish operation on: {self._partner_publisher}/{self._partner_offer}')


if __name__ == '__main__':
    cli_command.main()
