# SPDX-License-Identifier: GPL-2.0-or-later

import json
import logging
import xml.etree.ElementTree as ET

from datetime import datetime
from itertools import islice
from libcloud.common.aws import SignedAWSConnection, AWSDriver
from libcloud.common.base import Response
from libcloud.common.exceptions import BaseHTTPError
from libcloud.utils.xml import fixxpath
from math import ceil

NAMESPACE = 'http://ssm.amazonaws.com/doc/2014-11-06/'
SSM_TARGET_BASE = 'AmazonSSM'

MAX_DELETE_BATCH_SIZE = 10


class SSMValueException(ValueError):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class SSMParameter():
    def __init__(self, name, datatype, value, version, last_modified, arn):
        self.name = name
        self.datatype = datatype
        self.value = value
        self.version = version
        self.last_modified = datetime.fromisoformat(last_modified)
        self.arn = arn


class SSMDriver(AWSDriver):
    name = 'ssm'
    region_name = ''


class GetParametersByPathResponse(Response):
    def __init__(self, r):
        logging.debug(f'Creating a new GetParametersByPathResponse object with {r}')
        self.r = r

    def parameters(self):
        return self.r.parse_body()


class DeleteParametersResponse(Response):
    def __init__(self, r):
        self.r = r


class SSMConnection(SignedAWSConnection):
    version = '2014-11-06'
    driver = SSMDriver
    service_name = 'ssm'
    region_name = ''

    def __init__(self, access_key_id=None, secret_key=None, region="us-east-1", token=None, signature_version=4):
        self.token = token
        self.region_name = region
        host = "ssm.{}.amazonaws.com".format(region)
        super(SSMConnection, self).__init__(access_key_id, secret_key, host=host,
                                            token=self.token, signature_version=signature_version)
        self.driver.region_name = self.region_name

    @property
    def region(self):
        return self.region_name

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
            raise

    def _get_parameters_by_path_paginated(self,
                                          path,
                                          recursive=False,
                                          max_results=10,
                                          ):
        """Return an array of SSMVariable objects. May invoke multiple API calls"""
        retval = []
        more = True
        next_token = ""
        while more:
            max_results_param = min(10, max_results - len(retval))
            params = {'Action': 'GetParametersByPath',
                      'Path': path,
                      'Recursive': 'true',
                      'MaxResults': max_results_param,
                      }
            if len(next_token) > 0:
                params['NextToken'] = next_token
            try:
                response = GetParametersByPathResponse(self.request('/', params=params))
            except BaseHTTPError as e:
                logging.error(f'Unable to query parameter path {path}: {e.message}')
                raise

            x = response.parameters()
            root = ET.fromstring(x)
            y = root.findall(fixxpath('GetParametersByPathResult', namespace=NAMESPACE))

            for el in y:
                tag = el.find(fixxpath('NextToken', namespace=NAMESPACE))
                if tag is not None:
                    next_token = tag.text
                else:
                    next_token = ""
                params = el.find(fixxpath('Parameters', namespace=NAMESPACE))
                members = params.findall(fixxpath('member', namespace=NAMESPACE))
                for var in members:
                    name = var.find(fixxpath('Name', namespace=NAMESPACE)).text
                    last_modified = var.find(fixxpath('LastModifiedDate', namespace=NAMESPACE)).text
                    datatype = var.find(fixxpath('DataType', namespace=NAMESPACE)).text
                    ver = var.find(fixxpath('Version', namespace=NAMESPACE)).text
                    value = var.find(fixxpath('Value', namespace=NAMESPACE)).text
                    arn = var.find(fixxpath('ARN', namespace=NAMESPACE)).text
                    obj = SSMParameter(name, datatype, value, ver, last_modified, arn)
                    retval.append(obj)

            if len(retval) >= max_results or len(next_token) == 0:
                more = False

        return retval

    def get_parameters_by_path(self,
                               path,
                               recursive=False,
                               max_results=10,
                               ):
        """Return an array of SSMVariable objects"""
        return self._get_parameters_by_path_paginated(path,
                                                      recursive=recursive,
                                                      max_results=max_results)

    def _build_parameter_list(self, params):
        """Return a list of dictionaries with query parameters
        suitable for passing to AmazonSSM.DeleteParameters

        """
        retval = {}
        for idx, param in enumerate(params):
            idx += 1  # We want 1-based indexes
            if not isinstance(param, SSMParameter):
                raise AttributeError(
                    'param %s in parameters '
                    'not an SSMParameter' % param)
            retval[f'Names.{idx}'] = param.name
        return retval

    def _get_headers(self, action):
        """
        Get the default headers for a request to the ECS API
        """
        return {'x-amz-target': '%s.%s' %
                (SSM_TARGET_BASE, action),
                'Content-Type': 'application/x-amz-json-1.1'
                }

    def delete_parameters(self, parameters=[], dry_run=False):
        """Wrapper around the DeleteParameters API with handling for arbitrary parameter list lengths."""
        slicelen = MAX_DELETE_BATCH_SIZE
        slices = ceil(len(parameters) / slicelen)
        logging.debug(f'Called delete_parameters with {len(parameters)} candidates')
        for start in range(0, slices):
            s = [e for e in islice(parameters, start * slicelen, start * slicelen + slicelen)]
            res = self._delete_parameters(s, dry_run)
            if not res.success():
                logging.warn(f'Deleting {s}, got error {res.parse_error()}')

    def _delete_parameters(self, parameters=[], dry_run=False):
        """Call the DeleteParameters API"""

        logging.debug(f'Called _delete_parameters() with {len(parameters)} parameters')
        if dry_run:
            logging.info(f'DRY RUN. Would delete {len(parameters)} parameters')
            return DeleteParametersResponse(None)
        if len(parameters) <= 0:
            return DeleteParametersResponse(None)
        if len(parameters) > MAX_DELETE_BATCH_SIZE:
            msg = f'delete_parameters was given {len(parameters)} items, max = 10'
            raise SSMValueException(msg)

        action = 'DeleteParameters'
        data = {
            'Names': [p.name for p in parameters]
        }
        headers = self._get_headers(action)
        j = json.dumps(data)
        return DeleteParametersResponse(self.request('/', headers=headers, data=j, method='POST'))
