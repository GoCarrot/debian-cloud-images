import logging
import pathlib

from .base import BaseCommand
from ..images import Images
from ..utils.libcloud.other.aws_ssm import SSMConnection


class SSMVariableSetter:

    def __init__(self, access_key_id, secret_key, token, images, prefix, force_overwrite=False, dry_run=False):
        self.images = images
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.token = token
        self.prefix = prefix
        self.force_overwrite = force_overwrite
        self.dry_run = dry_run
        self.__regional_connections = {}

    def __call__(self):
        release_id = None
        release_name = None

        # Keep track of keys we've already set, per region
        regional_keys = {}

        for image in self.images.values():
            try:
                release_id = image.build_release_id
                release_name = image.build_release
                release_arch = image.build_arch
            except IndexError:
                logging.info(f'no builds for {image.name}')

            for upload in image.uploads:

                # Note that some currently unsupported AWS regions
                # will likely require a more sophisticated check.  For
                # example, regions in China are under the .cn ccTLD
                if not upload.provider.endswith("amazonaws.com"):
                    logging.info(f'Skipping {upload.provider} upload')
                    continue

                region = upload.metadata.labels['aws.amazon.com/region']
                if region not in regional_keys.keys():
                    regional_keys[region] = {}
                logging.debug("Region: {}".format(region))
                for version, overwrite in [['latest',
                                            True],
                                           [upload.metadata.labels['cloud.debian.org/version'],
                                            False]]:
                    overwrite = overwrite | self.force_overwrite
                    for release in [release_name, release_id]:
                        key = "{}/{}/{}/{}/{}".format(
                            self.prefix,
                            upload.metadata.labels['upload.cloud.debian.org/type'],
                            release,
                            version,
                            release_arch,
                        )
                        value = upload.ref
                        if key in regional_keys[region]:
                            logging.info("Skipping already set key {}".format(key))
                            continue

                        regional_keys[region][key] = value
                        logging.info("Setting {}={} (region={}, overwrite={})".format(
                            key, value, region, overwrite))
                        if self.dry_run:
                            logging.info("Dry-run: set {}={}, overwrite={}".format(key, value, overwrite))
                        else:
                            self.connection(region).set_variable(key, value, overwrite=overwrite)

    def connection(self, region):
        if region not in self.__regional_connections:
            self.__regional_connections[region] = SSMConnection(
                self.access_key_id,
                self.secret_key,
                region=region,
                token=self.token,
                signature_version=4,
            )
        return self.__regional_connections[region]


class PutSSMCommand(BaseCommand):
    argparser_name = 'put-ssm'
    argparser_help = 'set AWS SSM variable values'
    argparser_epilog = '''
config options:
  ec2.ssm.prefix     store AMI details relative to the given SSM path
'''

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            'manifests',
            help='read manifests',
            metavar='MANIFEST',
            nargs='*',
            type=pathlib.Path
        )

        parser.add_argument(
            '--dry-run',
            help="Dry run mode, don't actually do anything",
            action='store_true',
            dest='dry_run',
        )

        parser.add_argument(
            '--force-overwrite',
            help='forcibly overwrite any existing value',
            action='store_true',
            dest='force_overwrite',
        )

    def __init__(self, manifests=[], prefix=None, regions=[], force_overwrite=False, dry_run=False, **kw):
        super().__init__(**kw)

        self.ssm_prefix = self.config_get('ec2.ssm.prefix')
        self.images = Images()
        for manifest in manifests:
            self.images.read(manifest)
        self.setter = SSMVariableSetter(
            access_key_id=self.config_get('ec2.auth.key'),
            secret_key=self.config_get('ec2.auth.secret'),
            token=self.config_get('ec2.auth.token', default=None),
            images=self.images,
            prefix=self.ssm_prefix,
            force_overwrite=force_overwrite,
            dry_run=dry_run,
        )

    def __call__(self):
        self.setter()


if __name__ == '__main__':
    PutSSMCommand._main()
