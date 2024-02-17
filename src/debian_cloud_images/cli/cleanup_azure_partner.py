# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import logging

from debian_cloud_images.images.azure_partnerlegacy.s1_offer import ImagesAzurePartnerlegacyOffer
from debian_cloud_images.images.azure_storage.s1_folder import ImagesAzureStorageFolder
from debian_cloud_images.utils.azure.image_version import AzureImageVersion
from debian_cloud_images.utils.libcloud.common.azure import AzureGenericOAuth2Connection
from debian_cloud_images.utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver

from .base import cli, BaseCommand

logger = logging.getLogger(__name__)


@cli.register(
    'cleanup-azure-partner',
    help='cleanup Azure Partner offers',
    epilog='''
config options:
  azure.auth.client     application ID of service account, or empty for using az
  azure.auth.secret     secret of service account, or empty for using az
  azure.cloudpartner.tenant
  azure.cloudpartner.publisher
  azure.storage.tenant
  azure.storage.subscription
  azure.storage.group
  azure.storage.name
''',
    arguments=[
        cli.prepare_argument(
            '--partner-offer',
            help='use specified offer inside Azure Partner interface',
            metavar='OFFER',
            required=True,
        ),
        cli.prepare_argument(
            '--offer-delete-after',
            dest='delete_after_offer',
            help='delete images from offers after X days',
            metavar='DAYS',
            type=int,
        ),
        cli.prepare_argument(
            '--storage-delete-after',
            dest='delete_after_storage',
            help='delete images from storage after X days',
            metavar='DAYS',
            type=int,
        ),
        cli.prepare_argument(
            '--no-op',
            action='store_true',
        ),
    ],
)
class CleanupAzurePartnerlegacyCommand(BaseCommand):
    def __init__(
            self, *,
            no_op: bool,
            partner_offer: str,
            delete_after_offer: int,
            delete_after_storage: int,
            date_today=datetime.date.today(),
            **kw,
    ):
        super().__init__(**kw)

        self.no_op = no_op
        self._partner_offer = partner_offer
        self._storage_folder = partner_offer

        self._client_id = str(self.config_get('azure.auth.client', default=None))
        self._client_secret = self.config_get('azure.auth.secret', default=None)

        self._partner_tenant = str(self.config_get('azure.cloudpartner.tenant'))
        self._partner_publisher = self.config_get('azure.cloudpartner.publisher')

        self._storage_tenant = str(self.config_get('azure.storage.tenant'))
        self._storage_subscription = str(self.config_get('azure.storage.subscription'))
        self._storage_group = self.config_get('azure.storage.group')
        self._storage_name = self.config_get('azure.storage.name')

        if delete_after_offer:
            self.delete_date_offer = date_today - datetime.timedelta(days=delete_after_offer)
        else:
            self.delete_date_offer = None

        if delete_after_storage:
            self.delete_date_storage = date_today - datetime.timedelta(days=delete_after_storage)
        else:
            self.delete_date_storage = None

    def __call__(self):
        partner_conn = AzureGenericOAuth2Connection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._partner_tenant,
            subscription_id=None,
            host='cloudpartner.azure.com',
            login_resource='https://cloudpartner.azure.com',
        )
        storage_driver = AzureResourceManagementStorageDriver(
            client_id=self._client_id,
            client_secret=self._client_secret,
            tenant_id=self._storage_tenant,
            subscription_id=self._storage_subscription,
        )
        storage_obj = storage_driver.get_storage(
            self._storage_name,
            self._storage_group,
        )

        partner_offer = ImagesAzurePartnerlegacyOffer(
            self._partner_publisher,
            self._partner_offer,
            partner_conn,
        )
        image_folder = ImagesAzureStorageFolder(
            self._storage_group,
            self._storage_name,
            self._storage_folder,
            storage_driver,
            storage_obj,
        )

        if self.delete_date_offer:
            print(f'Deleting images from offer {self._partner_offer} before {self.delete_date_offer.strftime("%Y-%m-%d")}')
            partner_offer.op_cleanup(self.__remove_offer)
        else:
            print('Not deleting images from offer')

        if self.delete_date_storage:
            print(f'Deleting images from storage before {self.delete_date_storage.strftime("%Y-%m-%d")}')
            image_folder.op_cleanup(self.__remove_storage)
        else:
            print('Not deleting images from storage (not implemented!)')

    def __remove_offer(self, version_str: str) -> bool:
        version = AzureImageVersion.from_string(version_str)
        date: datetime.date = datetime.datetime.strptime(str(version.minor), '%Y%m%d').date()
        if date >= self.delete_date_offer:
            logger.debug(f'Not deleting image {version} from offer, too new')
        else:
            print(f'Deleting image {version} from offer')
            if not self.no_op:
                return True
        return False

    def __remove_storage(self, modified: datetime.datetime) -> bool:
        date: datetime.date = modified.date()
        if date >= self.delete_date_storage:
            logger.debug(f'Not deleting file last modified {date} from storage, too new')
        else:
            print(f'Deleting file last modified {date} from storage')
            if not self.no_op:
                return True
        return False


if __name__ == '__main__':
    cli.main(CleanupAzurePartnerlegacyCommand)
