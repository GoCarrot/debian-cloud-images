# SPDX-License-Identifier: GPL-2.0-or-later

import requests
import typing
import urllib.parse

from libcloud.common.aws import AWSDriver
from libcloud.storage.drivers.s3 import BaseS3StorageDriver, S3SignatureV4Connection


class S3BucketStorageDriver(AWSDriver, BaseS3StorageDriver):
    name = 'Amazon S3 (virtual host)'
    connectionCls: typing.Type = S3SignatureV4Connection

    def __init__(self, bucket, key, secret=None, region=None, **kwargs):
        host, self.region_name = self._get_host_region(bucket)
        super().__init__(key=key, secret=secret, host=host, **kwargs)

    def _get_host_region(self, bucket):
        """ Detect bucket host and region from unauthenticated request """
        host = '{}.s3.amazonaws.com'.format(bucket)

        r = requests.head('https://{}/'.format(host), allow_redirects=False)

        if r.status_code in (200, 403):
            region = r.headers['x-amz-bucket-region']
        elif r.status_code in (307, ):
            host = urllib.parse.urlsplit(r.headers['location']).netloc
            region = r.headers['x-amz-bucket-region']
        else:
            raise RuntimeError(r.status_code)

        return host, region

    def _get_container_path(self, container):
        if container:
            return '/%s' % (container.name)
        else:
            return ''
