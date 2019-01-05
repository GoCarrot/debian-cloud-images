import http.client

from libcloud.common.base import Connection
from libcloud.common.aws import AWSDriver
from libcloud.storage.drivers.s3 import BaseS3StorageDriver, S3SignatureV4Connection


class S3BucketStorageDriver(AWSDriver, BaseS3StorageDriver):
    name = 'Amazon S3 (virtual host)'
    connectionCls = S3SignatureV4Connection

    def __init__(self, bucket, key, secret=None, region=None, **kwargs):
        host = '{}.s3.amazonaws.com'.format(bucket)
        self.region_name = self._get_region(host)
        super().__init__(key=key, secret=secret, host=host, **kwargs)

    def _get_region(self, host):
        """ Detect bucket region from unauthenticated request """
        connection = Connection(host=host)

        r = connection.request('/', method='HEAD', raw=True)

        if r.status in (http.client.OK, http.client.FORBIDDEN):
            return r.headers['x-amz-bucket-region']

        raise RuntimeError(r.status)

    def _get_container_path(self, container):
        if container:
            return '/%s' % (container.name)
        else:
            return ''
