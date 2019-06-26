import datetime
import logging

from libcloud.common.exceptions import BaseHTTPError

from .base import BaseCommand
from ..utils import argparse_ext
from ..utils.azure.image_version import AzureImageVersion
from ..utils.libcloud.other.azure_cloudpartner import AzureCloudpartnerOAuth2Connection
from ..utils.libcloud.storage.azure_arm import AzureResourceManagementStorageDriver


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
        self.plans = {i['planId']: i for i in self.data['definition']['plans']}

    def save(self):
        r = self._request(data=self.data, method='PUT', headers={'If-Match': self.etag})
        return r.parse_body()


class DeleteAzureCloudpartnerCommand(BaseCommand):
    argparser_name = 'delete-azure-cloudpartner'
    argparser_help = 'delete Debian images published via Azure Cloud Partner interface'

    @classmethod
    def _argparse_register(cls, parser, config):
        super()._argparse_register(parser, config)

        parser.add_argument(
            '--publisher',
            dest='publisher_id',
            help='Azure publisher',
            metavar='PUBLISHER',
        )
        parser.add_argument(
            '--offer',
            action='append',
            dest='offer_ids',
            help='Azure offer, can be specified multiple times',
            metavar='OFFER',
        )
        parser.add_argument(
            '--storage',
            dest='storage_id',
            help='Name or ID of Azure storage',
            metavar='ID',
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
            '--auth',
            action=argparse_ext.ActionAzureAuth,
            required=True,
        )
        parser.add_argument(
            '--no-op',
            action='store_true',
        )

    def __init__(
            self, *,
            publisher_id,
            offer_ids,
            storage_id,
            auth,
            delete_after_offer=None,
            delete_after_storage=None,
            no_op=False,
            date_today=datetime.datetime.now(),
            **kw,
    ):
        super().__init__(**kw)

        self.publisher_id = publisher_id
        self.offer_ids = offer_ids or []
        self.storage_id = storage_id
        self.auth = auth
        self.no_op = no_op

        if delete_after_offer:
            self.delete_date_offer = date_today - datetime.timedelta(days=delete_after_offer)
        else:
            self.delete_date_offer = None

        if delete_after_storage:
            self.delete_date_storage = date_today - datetime.timedelta(days=delete_after_storage)
        else:
            self.delete_date_storage = None

        self.__cloudpartner = self.__storage = None

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

    @property
    def storage(self):
        ret = self.__storage
        if ret is None:
            storage_driver = AzureResourceManagementStorageDriver(
                tenant_id=self.auth.tenant_id,
                subscription_id=None,
                client_id=self.auth.client_id,
                client_secret=self.auth.client_secret,
            )
            ret = self.__storage = storage_driver.get_storage(
                self.storage_id,
            )
        return ret

    def delete_from_offer(self):
        for offer_id in self.offer_ids:
            self._delete_from_offer(offer_id)

    def _delete_from_offer(self, offer_id):
        logging.debug(f'Deleting images from offer {offer_id}')

        offer = AzureCloudPartnerOffer(self.cloudpartner, self.publisher_id, offer_id)
        changed = False
        for plan_id, plan in offer.plans.items():
            changed |= self._delete_from_offer_plan(plan_id, plan)

        if changed:
            if not self.no_op:
                logging.info(f'Save offer {offer_id}')
                offer.save()
            else:
                logging.info(f'Would save offer {offer_id}')
        else:
            logging.debug(f'Would not save unmodified offer {offer_id}')

    def _delete_from_offer_plan(self, plan_id, plan):
        changed = False

        logging.debug(f'Deleting images from plan {plan_id}')

        images = plan['microsoft-azure-corevm.vmImagesPublicAzure']
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
        pass
# TODO: libcloud fails to extract last modified
#        for c in self.storage.iterate_containers():
#            last_modified = c.extra['last_modified']
#            logging.debug(f'Container {c.name} last modified {last_modified}')


if __name__ == '__main__':
    DeleteAzureCloudpartnerCommand._main()
