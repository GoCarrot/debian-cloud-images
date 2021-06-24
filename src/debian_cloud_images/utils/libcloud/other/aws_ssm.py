import logging
import sys

from libcloud.common.aws import SignedAWSConnection, AWSDriver
from libcloud.common.exceptions import BaseHTTPError


class SSMDriver(AWSDriver):
    name = 'ssm'
    region_name = ''


class SSMConnection(SignedAWSConnection):
    version = '2014-11-06'
    driver = SSMDriver
    service_name = 'ssm'
    region_name = ''

    def __init__(self, access_key_id, secret_key, region, token, signature_version=4):
        self.token = token
        self.region_name = region
        host = "ssm.{}.amazonaws.com".format(region)
        super(SSMConnection, self).__init__(access_key_id, secret_key, host=host,
                                            token=self.token, signature_version=signature_version)

    def set_variable(self, name, value, type='String', overwrite=False):
        overwrite_param = 'false'
        if overwrite:
            overwrite_param = 'true'

        self.driver.region_name = self.region_name

        params = {'Action': 'PutParameter',
                  'Type': type,
                  'Name': name,
                  'Value': value,
                  'Overwrite': overwrite_param,
                  'Version': '2016-11-15',
                  }
        try:
            self.request(
                '/',
                params=params,
            )
        except BaseHTTPError as e:
            logging.error(f'Unable to set variable {name}: {e.message}')
            sys.exit(1)
