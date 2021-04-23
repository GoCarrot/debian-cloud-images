import datetime
import logging

from collections import namedtuple

from .base import BaseCommand
from ..images.azure_partner import AzurePartnerImages
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection
from ..utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver


AzureAuth = namedtuple('AzureAuth', ('client', 'secret'))
AzureCloudpartner = namedtuple('AzureCloudpartner', ('tenant', 'publisher'))
AzureStorage = namedtuple('AzureStorage', ('tenant', 'subscription', 'group', 'name'))


class CleanupAzureCloudpartnerCommand(BaseCommand):
    argparser_name = 'cleanup-azure-cloudpartner'
    argparser_help = 'cleanup Debian images published via Azure Cloud Partner interface'
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
        )
        parser.add_argument(
            '--offer-delete-after',
            dest='delete_after_offer',
            help='Delete images from offers after X days',
            metavar='DAYS',
            type=int,
        )
        parser.add_argument(
            '--storage-delete-after',
            dest='delete_after_storage',
            help='Delete images from storage after X days',
            metavar='DAYS',
            type=int,
        )
        parser.add_argument(
            '--no-op',
            action='store_true',
        )

    def __init__(
            self, *,
            offer_ids=[],
            delete_after_offer=None,
            delete_after_storage=None,
            no_op=False,
            date_today=datetime.datetime.now(),
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
        self.storage = AzureStorage(
            tenant=str(self.config_get('azure.storage.tenant')),
            subscription=str(self.config_get('azure.storage.subscription')),
            group=self.config_get('azure.storage.group'),
            name=self.config_get('azure.storage.name'),
        )

        self.offer_ids = offer_ids
        self.no_op = no_op

        if delete_after_offer:
            self.delete_date_offer = date_today - datetime.timedelta(days=delete_after_offer)
        else:
            self.delete_date_offer = None

        if delete_after_storage:
            self.delete_date_storage = date_today - datetime.timedelta(days=delete_after_storage)
        else:
            self.delete_date_storage = None

        self.__cloudpartner_obj = self.__storage_obj = None

    def __call__(self):
        if self.delete_date_offer:
            logging.info(f'Deleting images from offers before {self.delete_date_offer.strftime("%Y-%m-%d")}')
            AzurePartnerImages(self.no_op, None, self.cloudpartner.publisher, self.cloudpartner_obj).cleanup(self.offer_ids, self.delete_date_offer)
        else:
            logging.info('Not deleting images from offers')

        if self.delete_date_storage:
            logging.info(f'Deleting images from storage before {self.delete_date_storage.strftime("%Y-%m-%d")}')
            self.delete_from_storage()
        else:
            logging.info('Not deleting images from storage')

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

    @property
    def storage_obj(self):
        ret = self.__storage_obj
        if ret is None:
            storage_driver = AzureResourceManagementStorageDriver(
                tenant_id=self.storage.tenant,
                subscription_id=self.storage.subscription,
                client_id=self.auth.client,
                client_secret=self.auth.secret,
            )
            ret = self.__storage = storage_driver.get_storage(
                name=self.storage.name,
                resource_group=self.storage.group,
            )
        return ret

    def delete_from_storage(self):
        for c in self.storage_obj.iterate_containers():
            # XXX: libcloud fails to extract last modified
            # last_modified = c.extra['last_modified']

            try:
                name_prefix, name_date, name_id = c.name.rsplit('-', 2)
                date = datetime.datetime.strptime(name_date, '%Y%m%d')
            except ValueError:
                logging.warning(f'Not deleting file {c.name}, unable to parse name')
                continue

            if date >= self.delete_date_storage:
                logging.debug(f'Not deleting image {c.name}, too new')
            else:
                if not self.no_op:
                    logging.info(f'Deleting image {c.name}')
                    for f in c.iterate_objects():
                        self.storage.delete_object(f)
                    self.storage.delete_container(c)
                else:
                    logging.info(f'Would deleting image {c.name}')


if __name__ == '__main__':
    CleanupAzureCloudpartnerCommand._main()
