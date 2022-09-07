#!/usr/bin/env python
# Kyle Fitzsimmons, 2018
from datetime import datetime, timedelta
import dateutil.parser
from decimal import Decimal
from faker import Factory
from flask import url_for
import json
import logging
import pytest
import pytz
import random

from mobile.database import Database
from tests.hardcoded_survey_questions import default_stack
from tests.test_mobile_create import test_create_mobile_user as create_mobile_user
from utils.data import camelcase_to_underscore, rename_json_keys, isclose


database = Database()
fake = Factory.create()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('test_mobile_update')
tz = pytz.timezone('America/Montreal')


# assertion helper functions
def assert_request_data_matches_db_record(request_dict, db_record, api_version=1):
    if api_version == 2:
        request_dict = rename_json_keys(request_dict, camelcase_to_underscore)

    for input_key, input_value in request_dict.items():
        response_value = getattr(db_record, input_key)
        if isinstance(response_value, Decimal):
            assert isclose(input_value, response_value, rel_tol=1e-03)
        elif isinstance(response_value, datetime):
            input_datetime = dateutil.parser.parse(input_value)
            assert input_datetime == response_value
        else:
            assert input_value == response_value


# no need to provide legacy test as previous version's static keys do not contain underscores 
# (all keys within returned `survey` schema will be user-generated)
def test_upsert_mobile_user_survey_response_legacy(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']
    schema = response.json['results']['survey']

    test_data = {
        'uuid': uuid,
        'survey': {
            'Age': 0,
            'Email': 'johnreilly@dean.com',
            'Gender': 0,
            'location_home': {'latitude': '16.1108045', 'longitude': '150.941385'},
            'location_study': {'latitude': '34.106815', 'longitude': '110.646193'},
            'location_work': {'latitude': '15.238540', 'longitude': '-100.787531'},
            'member_type': 2,
            'survey_textbox': 'Debitis corrupti iste corporis earum iure unde repudiandae.',
            'survey_checkboxes': ['Checkbox 1', 'Checkbox 2'],
            'survey_dropdown': ['A'],
            'survey_map': {'latitude': '49.9621115', 'longitude': '158.644588'},
            'survey_number': 6057,
            'travel_mode_alt_study': 6,
            'travel_mode_alt_work': 7,
            'travel_mode_study': 0,
            'travel_mode_work': 3
        }
    }

    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    user = database.user.find_by_uuid(uuid)
    survey_response = user.survey_response.one().response

    # check that non-hardcoded questions return the same values from
    # database as provided in the request
    for key, value in test_data['survey'].items():        
        for question in default_stack:
            if question['colName'] == key:
                break
        else:
            assert (survey_response[key] == value or [survey_response[key]] == value)


def test_add_mobile_user_coordinates(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    coordinates = [{
        'latitude': '45.5088872928',
        'longitude': '-73.6289835571',
        'speed': 17.37400388436377,
        'hAccuracy': 16,
        'vAccuracy': 25,
        'accelerationX': 0.10268011979651681,
        'accelerationY': 0.0158970260262572,
        'accelerationZ': 0.7714920319430699,
        'modeDetected': 1,
        'pointType': 8,
        'timestamp': '2018-04-24T00:25:13-04:00'
    }, {
        'latitude': '45.5302975702',
        'longitude': '-73.6479925378',
        'speed': 14.250232900155211,
        'hAccuracy': 9,
        'vAccuracy': 3,
        'accelerationX': 0.1880549662797817,
        'accelerationY': 0.4367783439516336,
        'accelerationZ': 0.04315788616135474,
        'modeDetected': 5,
        'pointType': 7,
        'timestamp': '2018-04-24T00:25:28-04:00'
    }]

    # submit coordinates to server
    test_data = {
        'uuid': uuid,
        'coordinates': coordinates
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    # check that a deprecation warning is provided for v1 api
    assert 'Warning (deprecated):' in r.json['status']

    # check that the same number of coordinates with all provided information are returned
    # from database with same attributes and order as provided
    user = database.user.find_by_uuid(uuid)
    assert user.mobile_coordinates.count() == 2

    for idx, db_coordinate in enumerate(user.mobile_coordinates):
        assert_request_data_matches_db_record(coordinates[idx], db_coordinate, api_version=2)


def test_add_mobile_user_coordinates_legacy(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    coordinates = [{
        'latitude': '45.5088872928',
        'longitude': '-73.6289835571',
        'speed': 17.37400388436377,
        'h_accuracy': 16,
        'v_accuracy': 25,
        'acceleration_x': 0.10268011979651681,
        'acceleration_y': 0.0158970260262572,
        'acceleration_z': 0.7714920319430699,
        'mode_detected': 1,
        'point_type': 8,
        'timestamp': '2018-04-24T00:25:13-04:00'
    }, {
        'latitude': '45.5302975702',
        'longitude': '-73.6479925378',
        'speed': 14.250232900155211,
        'h_accuracy': 9,
        'v_accuracy': 3,
        'acceleration_x': 0.1880549662797817,
        'acceleration_y': 0.4367783439516336,
        'acceleration_z': 0.04315788616135474,
        'mode_detected': 5,
        'point_type': 7,
        'timestamp': '2018-04-24T00:25:28-04:00'
    }]

    # submit coordinates to server
    test_data = {
        'uuid': uuid,
        'coordinates': coordinates
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    # check that a deprecation warning is provided for v1 api
    assert 'Warning (deprecated):' in r.json['status']

    # check that the same number of coordinates with all provided information are returned
    # from database with same attributes and order as provided
    user = database.user.find_by_uuid(uuid)
    assert user.mobile_coordinates.count() == 2

    for idx, db_coordinate in enumerate(user.mobile_coordinates):
        assert_request_data_matches_db_record(coordinates[idx], db_coordinate, api_version=1)


def test_add_mobile_user_cancelled_prompts(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    cancelled_prompts = [{
        'cancelledAt': None,
        'displayedAt': '2018-04-25T13:52:27-04:00',
        'isTravelling': None,
        'latitude': '45.5329431049',
        'longitude': '-73.5435169592',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }, {
        'cancelledAt': '2018-04-30T09:16:40-04:00',
        'displayedAt': '2018-04-30T09:16:40-04:00',
        'isTravelling': False,
        'latitude': '45.4603680276',
        'longitude': '-73.5162924098',
        'uuid': 'ef3a2924-b760-e84d-514c-7f73138ddbd7'
    }]

    test_data = {
        'uuid': uuid,
        'cancelledPrompts': cancelled_prompts
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    # check that the same number of cancelled prompts with all provided information are returned
    # from database with same attributes and order as provided
    user = database.user.find_by_uuid(uuid)
    assert user.cancelled_prompts.count() == 2

    for idx, db_cancelled_prompt in enumerate(user.cancelled_prompts):
        cancelled_prompts[idx]['prompt_uuid'] = cancelled_prompts[idx].pop('uuid')
        assert_request_data_matches_db_record(cancelled_prompts[idx], db_cancelled_prompt, api_version=2)


def test_add_mobile_user_cancelled_prompts_legacy(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    cancelled_prompts = [{
        'cancelled_at': None,
        'displayed_at': '2018-04-25T13:52:27-04:00',
        'is_travelling': None,
        'latitude': '45.5329431049',
        'longitude': '-73.5435169592',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }, {
        'cancelled_at': '2018-04-30T09:16:40-04:00',
        'displayed_at': '2018-04-30T09:16:40-04:00',
        'is_travelling': False,
        'latitude': '45.4603680276',
        'longitude': '-73.5162924098',
        'uuid': 'ef3a2924-b760-e84d-514c-7f73138ddbd7'
    }]

    test_data = {
        'uuid': uuid,
        'cancelledPrompts': cancelled_prompts  # this had an inconsistent camelcase key in v1 of API
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    # check that a deprecation warning is provided for v1 api
    assert 'Warning (deprecated):' in r.json['status']

    # check that the same number of cancelled prompts with all provided information are returned
    # from database with same attributes and order as provided
    user = database.user.find_by_uuid(uuid)
    assert user.cancelled_prompts.count() == 2

    for idx, db_cancelled_prompt in enumerate(user.cancelled_prompts):
        cancelled_prompts[idx]['prompt_uuid'] = cancelled_prompts[idx].pop('uuid')
        assert_request_data_matches_db_record(cancelled_prompts[idx], db_cancelled_prompt, api_version=1)


def test_error_add_prompt_missing_uuid(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    cancelled_prompts = [{
        'cancelled_at': None,
        'displayed_at': '2018-04-25T13:52:27-04:00',
        'is_travelling': None,
        'latitude': '45.5329431049',
        'longitude': '-73.5435169592',
    }]

    test_data = {
        'uuid': uuid,
        'cancelledPrompts': cancelled_prompts
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 400


def test_add_mobile_user_prompts(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    prompt_responses = [{
        'answer': ['Work'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 0,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '53add9eb-d149-37a9-55e9-039df262b88e'
    }, {
        'answer': ['Indifferent'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 1,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '53add9eb-d149-37a9-55e9-039df262b88e'
    }, {
        'answer': ['Home'],
        'displayedAt': '2018-04-30T05:13:23-04:00',
        'latitude': '45.5415987234',
        'longitude': '-73.5710220311',
        'promptNum': 0,
        'recordedAt': '2018-04-30T05:13:32-04:00',
        'uuid': '610e66d8-8505-c081-c55c-5f6274e50fdb'
    }, {
        'answer': ['Great'],
        'displayedAt': '2018-04-30T05:13:23-04:00',
        'latitude': '45.5415987234',
        'longitude': '-73.5710220311',
        'promptNum': 1,
        'recordedAt': '2018-04-30T05:13:32-04:00',
        'uuid': '610e66d8-8505-c081-c55c-5f6274e50fdb'
    }]

    test_data = {
        'uuid': uuid,
        'prompts': prompt_responses
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    # check that the same number of cancelled prompts with all provided information are returned
    # from database with same attributes and order as provided
    user = database.user.find_by_uuid(uuid)
    assert user.prompt_responses.count() == 4

    for idx, db_prompt_response in enumerate(user.prompt_responses):
        prompt_responses[idx]['prompt_uuid'] = prompt_responses[idx].pop('uuid')
        prompt_responses[idx]['response'] = prompt_responses[idx].pop('answer')
        assert_request_data_matches_db_record(prompt_responses[idx], db_prompt_response, api_version=2)


def test_add_mobile_user_prompts_legacy(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    prompt_responses = [{
        'answer': ['Work'],
        'displayed_at': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'prompt_num': 0,
        'recorded_at': '2018-04-25T18:04:37-04:00',
        'uuid': '53add9eb-d149-37a9-55e9-039df262b88e'
    }, {
        'answer': ['Indifferent'],
        'displayed_at': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'prompt_num': 1,
        'recorded_at': '2018-04-25T18:04:37-04:00',
        'uuid': '53add9eb-d149-37a9-55e9-039df262b88e'
    }, {
        'answer': ['Home'],
        'displayed_at': '2018-04-30T05:13:23-04:00',
        'latitude': '45.5415987234',
        'longitude': '-73.5710220311',
        'prompt_num': 0,
        'recorded_at': '2018-04-30T05:13:32-04:00',
        'uuid': '610e66d8-8505-c081-c55c-5f6274e50fdb'
    }, {
        'answer': ['Great'],
        'displayed_at': '2018-04-30T05:13:23-04:00',
        'latitude': '45.5415987234',
        'longitude': '-73.5710220311',
        'prompt_num': 1,
        'recorded_at': '2018-04-30T05:13:32-04:00',
        'uuid': '610e66d8-8505-c081-c55c-5f6274e50fdb'
    }]

    test_data = {
        'uuid': uuid,
        'prompts': prompt_responses
    }
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 201

    # check that a deprecation warning is provided for v1 api
    assert 'Warning (deprecated):' in r.json['status']

    # check that the same number of cancelled prompts with all provided information are returned
    # from database with same attributes and order as provided
    user = database.user.find_by_uuid(uuid)
    assert user.prompt_responses.count() == 4

    for idx, db_prompt_response in enumerate(user.prompt_responses):
        prompt_responses[idx]['prompt_uuid'] = prompt_responses[idx].pop('uuid')
        prompt_responses[idx]['response'] = prompt_responses[idx].pop('answer')
        assert_request_data_matches_db_record(prompt_responses[idx], db_prompt_response, api_version=1)


def test_upgrade_mobile_user_cancelled_prompts(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    # send a cancelled prompt to be upgraded in first request
    cancelled_prompts = [{
        'cancelledAt': None,
        'displayedAt': '2018-04-25T13:52:27-04:00',
        'isTravelling': None,
        'latitude': '45.5329431049',
        'longitude': '-73.5435169592',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }]
    cancelled_prompt_test_data = {'uuid': uuid, 'cancelledPrompts': cancelled_prompts}
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(cancelled_prompt_test_data), content_type='application/json')
    user = database.user.find_by_uuid(uuid)
    assert r.status_code == 201
    assert user.cancelled_prompts.count() == 1

    # send a subsequent prompt answer for cancelled prompt in second request
    prompt_responses = [{
        'answer': ['Work'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 0,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }, {
        'answer': ['Indifferent'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 1,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }]
    prompts_test_data = {'uuid': uuid, 'prompts': prompt_responses}
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(prompts_test_data), content_type='application/json')
    assert r.status_code == 201
    user = database.user.find_by_uuid(uuid)
    assert user.cancelled_prompts.count() == 0
    assert user.prompt_responses.count() == 2


def test_upgrade_mobile_user_cancelled_prompts_same_request(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    # send a cancelled prompt to be upgraded in same request as prompt answer
    cancelled_prompts = [{
        'cancelledAt': None,
        'displayedAt': '2018-04-25T13:52:27-04:00',
        'isTravelling': None,
        'latitude': '45.5329431049',
        'longitude': '-73.5435169592',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }]

    prompt_responses = [{
        'answer': ['Work'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 0,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }, {
        'answer': ['Indifferent'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 1,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }]
    prompts_test_data = {'uuid': uuid, 'cancelledPrompts': cancelled_prompts, 'prompts': prompt_responses}
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(prompts_test_data), content_type='application/json')
    assert r.status_code == 201
    user = database.user.find_by_uuid(uuid)
    assert user.cancelled_prompts.count() == 0
    assert user.prompt_responses.count() == 2


def test_edit_mobile_user_prompts(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    prompt_responses = [{
        'answer': ['Work'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 0,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }, {
        'answer': ['Indifferent'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5396452179',
        'longitude': '-73.6304455045',
        'promptNum': 1,
        'recordedAt': '2018-04-25T18:04:37-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }]
    prompts_test_data = {'uuid': uuid, 'prompts': prompt_responses}
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(prompts_test_data), content_type='application/json')
    assert r.status_code == 201
    user = database.user.find_by_uuid(uuid)
    assert user.prompt_responses.count() == 2

    edited_prompt_responses = [{
        'answer': ['Home'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5743928341',
        'longitude': '-73.6393328475',
        'promptNum': 0,
        'recordedAt': '2018-04-25T18:04:42-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }, {
        'answer': ['Great'],
        'displayedAt': '2018-04-25T18:02:35-04:00',
        'latitude': '45.5743928341',
        'longitude': '-73.6393328475',
        'promptNum': 1,
        'recordedAt': '2018-04-25T18:04:42-04:00',
        'uuid': '72be2e8e-7ee8-f1b0-f175-84bf034111d5'
    }]
    edited_prompts_test_data = {'uuid': uuid, 'prompts': edited_prompt_responses}
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(edited_prompts_test_data), content_type='application/json')
    assert r.status_code == 201
    user = database.user.find_by_uuid(uuid)
    assert user.prompt_responses.count() == 2

    for idx, db_prompt_response in enumerate(user.prompt_responses):
        edited_prompt_responses[idx]['prompt_uuid'] = edited_prompt_responses[idx].pop('uuid')
        edited_prompt_responses[idx]['response'] = edited_prompt_responses[idx].pop('answer')
        assert_request_data_matches_db_record(edited_prompt_responses[idx], db_prompt_response, api_version=2)


def test_empty_update_is_200(app, client, session):
    response = create_mobile_user(app, client, session)
    uuid = response.json['results']['uuid']

    test_data = {'uuid': uuid}
    url = url_for('api.update_v1')
    r = client.post(url, data=json.dumps(test_data), content_type='application/json')
    assert r.status_code == 200
