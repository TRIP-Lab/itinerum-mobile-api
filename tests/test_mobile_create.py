#!/usr/bin/env python
# Kyle Fitzsimmons, 2018
from flask import url_for
import json
import logging
import pytest


logging.basicConfig(level=logging.INFO)
log = logging.getLogger('test_mobile_create')


# create new user with camelCase variable names
def test_create_mobile_user(app, client, session):
    new_user_payload = {
        'lang': 'en',
        'surveyName': 'test',
        'user': {
            'uuid': '7077a34e-afe5-4c22-bd96-119256b7dc51',
            'itinerumVersion': '12c',
            'osVersion': '80.23',
            'model': 'iPhone 4s',
            'os': 'ios'
        }
    }

    url = url_for('api.create_v1')
    r = client.post(url, data=json.dumps(new_user_payload))
    assert r.status_code == 201

    assert r.json['results']['uuid'] == new_user_payload['user']['uuid']
    assert r.json['results']['lang'] == new_user_payload['lang']
    assert r.json['results']['defaultAvatar'] == '/assets/static/defaultAvatar.png'
    assert r.json['results']['recordAcceleration'] == True
    assert r.json['results']['recordMode'] == True
    assert r.json['results']['surveyName'] == 'test'
    assert len(r.json['results']['prompt']['prompts']) == 2
    assert len(r.json['results']['survey']) == 16
    assert 'Warning (deprecated):' in r.json['status']
    return r


# this should fail in future versions since updating existing users should return a different
# response than a newly created user. As designed now, both responses return 201.
def test_create_duplicate_mobile_user(app, client, session):
    test_create_mobile_user(app, client, session)
    test_create_mobile_user(app, client, session)


# create new user with underscores in variable names
def test_create_mobile_user_legacy(app, client, session):
    new_user_payload = {
        'lang': 'en',
        'survey_name': 'test',
        'user': {
            'uuid': '7077a34e-afe5-4c22-bd96-119256b7dc51',
            'itinerum_version': '12c',
            'os_version': '80.23',
            'model': 'iPhone 4s',
            'os': 'ios'
        }
    }

    url = url_for('api.create_v1')
    r = client.post(url, data=json.dumps(new_user_payload))
    assert r.status_code == 201

    assert r.json['results']['uuid'] == new_user_payload['user']['uuid']
    assert r.json['results']['lang'] == new_user_payload['lang']
    assert r.json['results']['defaultAvatar'] == '/assets/static/defaultAvatar.png'
    assert r.json['results']['recordAcceleration'] == True
    assert r.json['results']['recordMode'] == True
    assert r.json['results']['surveyName'] == 'test'
    assert len(r.json['results']['prompt']['prompts']) == 2
    assert len(r.json['results']['survey']) == 16
    assert 'Warning (deprecated):' in r.json['status']


def test_create_mobile_user_with_bad_survey_name(app, client, session):
    new_user_payload = {
        'lang': 'en',
        'surveyName': 'bad_test',
        'user': {
            'uuid': '7077a34e-afe5-4c22-bd96-119256b7dc51',
            'itinerumVersion': '12c',
            'osVersion': '80.23',
            'model': 'iPhone 4s',
            'os': 'ios'
        }
    }
    url = url_for('api.create_v1')
    r = client.post(url, data=json.dumps(new_user_payload))
    assert r.status_code == 410
