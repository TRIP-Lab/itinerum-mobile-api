#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
from flask import current_app, request
import logging

from utils.responses import Error

logger = logging.getLogger(__name__)


def invalid_JSON_handler(e):
    return Error(status_code=400,
                 headers=e.headers,
                 resource_type=e.resource_type,
                 errors=e.errors)


class InvalidJSONError(Exception):
    def __init__(self, headers, resource_type, errors, status_code=400):
        self.headers = headers
        self.resource_type = resource_type
        self.errors = errors
        self.status_code = status_code

    def __repr__(self):
        return '<InvalidJSONError %s>' % self.error


# Performs renaming and validation of json keys with a provided function.
# If no validation function given explicity (i.e., a None value is provided),
# rename key but automatically pass validation.
def validate_json(validations, headers, resource_type):
    validated = {}
    errors = []
    with current_app.app_context():
        if not request.json:
            errors.append('No JSON data supplied.')
        else:
            for v in validations:
                for parent_key, params in v.items():
                    key = params['key']
                    value = request.json.get(key)

                    if not params['validator']:
                        validated[parent_key] = value
                    elif params['validator'](value):
                        validated[parent_key] = value
                    else:
                        errors.append(params['error'])

    if errors:
        logger.info(errors)
        raise InvalidJSONError(headers, resource_type, errors)
    return validated


# test whether a json value is present and has any value,
# 0 is an acceptable value for integers
def value_exists(value):
    # Python 2/3
    try:
        if isinstance(value, basestring):
            return value.strip() != ''
    except NameError:
        if isinstance(value, str):
            return value.strip() != ''
    if isinstance(value, int):
        return True
    return False
