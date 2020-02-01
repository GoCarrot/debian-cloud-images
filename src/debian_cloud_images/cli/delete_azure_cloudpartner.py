import datetime
import logging

from collections import namedtuple
from libcloud.common.exceptions import BaseHTTPError

from .base import BaseCommand
from ..utils.azure.image_version import AzureImageVersion
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection
from ..utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver


AzureAuth = namedtuple('AzureAuth', ('client', 'secret'))
AzureCloudpartner = namedtuple('AzureCloudpartner', ('tenant', 'publisher'))
AzureStorage = namedtuple('AzureStorage', ('tenant', 'subscription', 'group', 'name'))


class AzureCloudPartnerOffer:
    def __init__(self, driver, publisher_id, offer_id):
        self.driver = driver
        self.publisher_id = publisher_id
        self.offer_id = offer_id

        self.offer_path = '/api/publishers/{}/offers/{}'.format(publisher_id, offer_id)

        self.read()

    def _request(self, params=None, headers=None, data=None, method='GET'):
        return self.driver.request(self.offer_path, headers=headers, params=params, data=data, method=method)

    def publish(self, email):
        data = {
            'metadata': {
                'notification-emails': email,
            },
        }
        try:
            self.driver.request(self.offer_path + '/publish', data=data, method='POST')
        except BaseHTTPError as e:
            logging.error(f'Unable to publish offer: {e.message}')

    def read(self):
        r = self._request()
        self.data, self.etag = r.parse_body(), r.headers['etag']
        self.plans = {}
        for plan in self.data['definition']['plans']:
            images = {plan['planId']: plan['microsoft-azure-corevm.vmImagesPublicAzure']}
            for generation in plan['diskGenerations']:
                images[generation['planId']] = generation['microsoft-azure-corevm.vmImagesPublicAzure']
            self.plans[plan['planId']] = images

    def save(self):
        r = self._request(data=self.data, method='PUT', headers={'If-Match': self.etag})
        return r.parse_body()


class DeleteAzureCloudpartnerCommand(BaseCommand):
    argparser_name = 'delete-azure-cloudpartner'
    argparser_help = 'delete Debian images published via Azure Cloud Partner interface'
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
            self.delete_from_offer()
        else:
            logging.info(f'Not deleting images from offers')

        if self.delete_date_storage:
            logging.info(f'Deleting images from storage before {self.delete_date_storage.strftime("%Y-%m-%d")}')
            self.delete_from_storage()
        else:
            logging.info(f'Not deleting images from storage')

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

    def delete_from_offer(self):
        for offer_id in self.offer_ids:
            self._delete_from_offer(offer_id)

    def _delete_from_offer(self, offer_id):
        logging.debug(f'Deleting images from offer {offer_id}')

        offer = AzureCloudPartnerOffer(self.cloudpartner_obj, self.cloudpartner.publisher, offer_id)
        changed = False
        for plan in offer.plans.values():
            changed |= self._delete_from_offer_plan(plan)

        if changed:
            if not self.no_op:
                logging.info(f'Save offer {offer_id}')
                offer.save()
            else:
                logging.info(f'Would save offer {offer_id}')
        else:
            logging.debug(f'Would not save unmodified offer {offer_id}')

    def _delete_from_offer_plan(self, plan):
        changed = False

        for plan_id, images in plan.items():
            logging.debug(f'Deleting images from plan {plan_id}')

            versions_all = frozenset(AzureImageVersion.from_string(i) for i in images)
            versions_remain = set()

            for version in sorted(versions_all, reverse=True):
                if version.minor == 0:
                    logging.warning(f'Not deleting images from plan {plan_id}, undated images found')
                    return False
                date = datetime.datetime.strptime(str(version.minor), '%Y%m%d')
                if date >= self.delete_date_offer:
                    logging.debug(f'Not deleting image {version} from plan {plan_id}, too new')
                    versions_remain.add(version)
                else:
                    break

            for version in sorted(versions_all - versions_remain):
                if len(images) > 1:
                    logging.info(f'Deleting image {version} from plan {plan_id}')
                    del images[str(version)]
                    changed = True
                else:
                    logging.debug(f'Not deleting image {version} from plan {plan_id}, last remaining')

        return changed

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
    DeleteAzureCloudpartnerCommand._main()
