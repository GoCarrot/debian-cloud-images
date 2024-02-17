# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import pathlib

from .base import cli, BaseCommand
from ..images import Images
from ..utils.libcloud.other.aws_ssm import SSMConnection
from ..utils.retry import with_retries


class SSMVariableSetter:
    def __init__(self, access_key_id, secret_key, token, images, prefix, config_image, force_overwrite=False, dry_run=False, only_regions=None):
        self.images = images
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.token = token
        self.prefix = prefix
        self.config_image = config_image
        self.force_overwrite = force_overwrite
        self.dry_run = dry_run
        self.only_regions = []
        self.__regional_connections = {}

        if only_regions is not None:
            self.only_regions = only_regions.split(',')

    def __call__(self):

        # Keep track of keys we've already set, per region
        regional_keys = {}

        put_errors = 0
        for image in self.images.values():
            for upload in image.uploads:

                # Note that some currently unsupported AWS regions
                # will likely require a more sophisticated check.  For
                # example, regions in China are under the .cn ccTLD
                if not upload.provider.endswith("amazonaws.com"):
                    logging.info(f'Skipping {upload.provider} upload')
                    continue

                release_name = upload.metadata.labels['debian.org/release']
                releasemd = self.config_image.releases.get(release_name)

                release_id = releasemd.id
                region = upload.metadata.labels['aws.amazon.com/region']
                release_arch = upload.metadata.labels['debian.org/arch']
                release_name = upload.metadata.labels['debian.org/release']

                if len(self.only_regions) > 0 and region not in self.only_regions:
                    logging.info(f'Region {region} is not in only_regions, skipping')
                    continue

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
                            try:
                                with_retries(lambda: self.connection(region).set_variable(key,
                                                                                          value,
                                                                                          overwrite=overwrite),
                                             max_tries=4)
                            except Exception:
                                logging.error("Unable to set {}={} in {}".format(
                                    key, value, region))
                                put_errors += 1
        if put_errors > 0:
            logging.error("Problems posting to SSM")
            exit(1)

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


@cli.register(
    'put-ssm',
    help='set AWS SSM variable values',
    epilog='''
config options:
  ec2.ssm.prefix     store AMI details relative to the given SSM path
''',
    arguments=[
        cli.prepare_argument(
            'manifests',
            help='read manifests',
            metavar='MANIFEST',
            nargs='*',
            type=pathlib.Path
        ),
        cli.prepare_argument(
            '--dry-run',
            help="Dry run mode, don't actually do anything",
            action='store_true',
            dest='dry_run',
        ),
        cli.prepare_argument(
            '--force-overwrite',
            help='forcibly overwrite any existing value',
            action='store_true',
            dest='force_overwrite',
        ),
        cli.prepare_argument(
            '--regions',
            help='limit actions to only the given regions (comma separated)',
            metavar='REGIONS',
            dest='only_regions',
        ),
    ],
)
class PutSSMCommand(BaseCommand):
    def __init__(self, manifests=[], prefix=None, regions=[], force_overwrite=False, dry_run=False, only_regions=None, **kw):
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
            config_image=self.config_image,
            force_overwrite=force_overwrite,
            dry_run=dry_run,
            only_regions=only_regions,
        )

    def __call__(self):
        self.setter()


if __name__ == '__main__':
    cli.main(PutSSMCommand)
