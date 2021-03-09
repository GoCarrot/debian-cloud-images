import logging
import time

from libcloud.compute.types import VolumeSnapshotState

from .upload_base import UploadBaseCommand
from ..api.cdo.upload import Upload
from ..api.wellknown import label_ucdo_provider, label_ucdo_type
from ..utils.libcloud.compute.ec2 import ExEC2NodeDriver
from ..utils.libcloud.storage.s3 import S3BucketStorageDriver


class ImageUploaderEc2:
    compute_cls = ExEC2NodeDriver
    storage_cls = S3BucketStorageDriver

    architecture_map = {
        'amd64': 'x86_64',
        'arm64': 'arm64',
    }

    def __init__(self, output, bucket, key, secret, token, regions, add_tags, permission_public):
        self.output = output
        self.bucket = bucket
        self.key = key
        self.secret = secret
        self.token = token
        self.regions = regions
        self.add_tags = add_tags or {}
        self.permission_public = permission_public

        self.__compute = self.__storage = None

    @property
    def compute(self):
        ret = self.__compute
        if ret is None:
            ret = self.__compute = {
                r.name: self.compute_cls(key=self.key, secret=self.secret, token=self.token, region=r.name)
                for r in self.compute_cls(key=self.key, secret=self.secret, token=self.token, region='us-east-1').ex_list_regions()
            }
        return ret

    def compute_regions(self, region_base):
        if self.regions:
            if 'all' in self.regions:
                # All regions specified, use complete list
                return self.compute

            # Explicit regions specified
            return {r: v for r, v in self.compute.items() if r in self.regions}

        # No regions specified, use region of bucket
        return {r: v for r, v in self.compute.items() if r == region_base}

    @property
    def storage(self):
        ret = self.__storage
        if ret is None:
            ret = self.__storage = self.storage_cls(bucket=self.bucket, key=self.key, secret=self.secret)
        return ret

    def __call__(self, image, public_info):
        name = public_info.vendor_name

        obj = self.upload_file(image, name)

        try:
            ec2_snapshot = self.import_snapshot(image, public_info, obj)
            ec2_snapshots = self.copy_snapshot(image, public_info, ec2_snapshot)
            ec2_images = self.create_image(image, public_info, ec2_snapshots)

            manifests = []
            for region, ec2_image in ec2_images.items():
                metadata = image.build.metadata.copy()
                metadata.labels['aws.amazon.com/region'] = region
                metadata.labels[label_ucdo_provider] = 'aws.amazon.com'
                metadata.labels[label_ucdo_type] = public_info.public_type.name

                manifests.append(Upload(
                    metadata=metadata,
                    provider=ec2_image.driver.connection.host,
                    ref=ec2_image.id,
                ))

            image.write_manifests('upload-ec2', manifests, output=self.output)

        finally:
            self.delete_file(image, obj)

    def generate_permissions(self, name):
        if self.permission_public:
            return {f'{name}.Add.1.Group': 'all'}
        else:
            return {f'{name}.Remove.1.Group': 'all'}

    def generate_tags(self, image, public_info):
        tags = self.add_tags.copy()
        tags.update({
            'Name': 'AMI {}'.format(public_info.vendor_name),
            'AMI': public_info.vendor_name,
            'ImageFamily': public_info.vendor_family,
            'ImageVersion': image.build_info['version'],
        })
        return tags

    def create_image(self, image, public_info, snapshots):
        """ Create images in all regions """

        ec2_images = {}

        for snapshot in snapshots:
            mapping = [{
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'SnapshotId': snapshot.id,
                    'VolumeType': 'gp2',
                    'DeleteOnTermination': 'true',
                },
            }]

            driver = snapshot.driver
            architecture = self.architecture_map[image.build_arch]

            ec2_image = driver.ex_register_image(
                name=public_info.vendor_name,
                description=public_info.vendor_description,
                architecture=architecture,
                block_device_mapping=mapping,
                root_device_name='/dev/xvda',
                virtualization_type='hvm',
                ena_support=True,
                sriov_net_support='simple',
            )

            logging.info('Image %s/%s arch %s registered from %s', driver.region_name, ec2_image.id, architecture, snapshot.id)

            driver.ex_create_tags(ec2_image, self.generate_tags(image, public_info))
            driver.ex_modify_image_attribute(
                ec2_image,
                self.generate_permissions('LaunchPermission'),
            )

            ec2_images[driver.region_name] = ec2_image

        return ec2_images

    def copy_snapshot(self, image, public_info, snapshot_base):
        """ Copy snapshot to other regions """

        region_base = snapshot_base.driver.region_name
        compute_regions = self.compute_regions(region_base)

        snapshots_creating = []
        for region, compute in compute_regions.items():
            if region == region_base:
                snapshot = snapshot_base
            else:
                snapshot = compute.ex_copy_snapshot(
                    snapshot_base,
                    public_info.vendor_description,
                )

                logging.info('Copy snapshot to %s/%s', region, snapshot.id)

            compute.ex_create_tags(snapshot, self.generate_tags(image, public_info))
            compute.ex_modify_snapshot_attribute(
                snapshot,
                self.generate_permissions('CreateVolumePermission'),
            )

            snapshots_creating.append(snapshot)

        snapshots_available = []
        while len(snapshots_creating):
            snapshot = snapshots_creating.pop(0)
            snapshots_new = snapshot.driver.list_snapshots(snapshot)
            if not snapshots_new:
                snapshot_new = snapshot
            else:
                snapshot_new = snapshots_new[0]

            state = snapshot_new.state

            if state == VolumeSnapshotState.CREATING:
                time.sleep(15)
                snapshots_creating.append(snapshot_new)
            elif state == VolumeSnapshotState.AVAILABLE:
                logging.info('Snapshot %s/%s available', snapshot_new.driver.region_name, snapshot_new.id)
                snapshots_available.append(snapshot_new)
            else:
                logging.error('Snapshot %s/%s in unknown state', snapshot_new.driver.region_name, snapshot_new.id)

        return snapshots_available

    def import_snapshot(self, image, public_info, obj):
        """ Import file as snapshot in same region as bucket """

        region_name = obj.driver.region_name

        logging.info('Import snapshot to region %s', region_name)

        return self.compute[region_name].ex_import_snapshot(
            description=public_info.vendor_description,
            disk_container=[{
                'Description': 'root',
                'Format': 'VMDK',
                'UserBucket': {
                    'S3Bucket': self.bucket,
                    'S3Key': obj.name,
                }
            }],
        )

    def delete_file(self, image, obj):
        """ Delete file from storage """

        logging.info('Deleting file %s', obj.name)

        self.storage.delete_object(obj)

    def upload_file(self, image, name):
        """ Upload file to storage """

        file_out = '{}.vmdk'.format(name)

        logging.info('Uploading file to %s/%s', self.bucket, file_out)

        with image.open_image('vmdk') as f:
            return self.storage.upload_object_via_stream(
                iterator=f,
                container=None,
                object_name=file_out,
                extra={'content_type': 'application/octet-stream'},
            )


class UploadEc2Command(UploadBaseCommand):
    argparser_name = 'upload-ec2'
    argparser_help = 'upload Debian images to Amazon EC2'
    argparser_epilog = '''
config options:
  ec2.storage.name     create temporary image file in this S3 bucket
'''

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            '--permission-public',
            action='store_true',
            help='Make snapshot and image public',
        )

    def __init__(self, *, regions=[], add_tags={}, permission_public, **kw):
        super().__init__(**kw)

        self.uploader = ImageUploaderEc2(
            output=self.output,
            bucket=self.config_get('ec2.storage.name'),
            key=self.config_get('ec2.auth.key'),
            secret=self.config_get('ec2.auth.secret'),
            token=self.config_get('ec2.auth.token', default=None),
            regions=self.config_get('ec2.image.regions', default=[]),
            add_tags=dict(tuple(i.split('=', 1)) for i in self.config_get('ec2.image.tags', default=[])),
            permission_public=permission_public,
        )


if __name__ == '__main__':
    UploadEc2Command._main()
