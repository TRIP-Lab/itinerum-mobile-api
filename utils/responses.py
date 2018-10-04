#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
from flask import current_app
from flask import Response as ResponseBase
import json


class JSONResponse(ResponseBase):
    charset = 'utf-8'
    default_mimetype = 'application/json'

    def __init__(self, status, status_code):
        super(JSONResponse, self).__init__()
        self.status = status
        self.status_code = status_code

    @staticmethod
    def _jsonify(data):
        indent = None
        separators = (',', ':')
        if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] or current_app.debug:
            indent = 2
            separators = (', ', ': ')
        return json.dumps(data, indent=indent, separators=separators)


class Success(JSONResponse):
    headers = {}
    res_dict = {}

    def __init__(self, status_code, headers, resource_type, body, status=None):
        super(Success, self).__init__('success', status_code)
        self.res_dict['status'] = status or 'success'
        self.res_dict['type'] = resource_type
        self.res_dict['results'] = body

        if headers:
            for key, value in headers.items():
                if key == 'Location':
                    with current_app.app_context():
                        if value.startswith('/'):
                            value = value[:-1]

                        value = '{prefix}/{route}'.format(
                            prefix=current_app.config['APPLICATION_ROOT'],
                            route=value)
                self.headers[key] = value

        self.set_data(self._jsonify(self.res_dict))
        assert 200 <= status_code < 300


class Error(JSONResponse):
    headers = {}
    res_dict = {}

    def __init__(self, status_code, headers, resource_type, errors):
        super(Error, self).__init__('error', status_code)
        self.res_dict['status'] = 'error'
        self.res_dict['type'] = resource_type
        self.res_dict['errors'] = errors

        if headers:
            for key, value in headers.items():
                if key == 'Location':
                    with current_app.app_context():
                        if value.startswith('/'):
                            value = value[:-1]

                        value = '{prefix}/{route}'.format(
                            prefix=current_app.config['APPLICATION_ROOT'],
                            route=value)
                self.headers[key] = value
        self.set_data(self._jsonify(self.res_dict))
        assert status_code < 200 or 300 <= status_code
