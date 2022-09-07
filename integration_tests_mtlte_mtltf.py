#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2016-2018
#
# Tests and dummy data uploading functions for mobile API
from datetime import datetime, timedelta
import dateutil.parser
from faker import Factory
import json
import pytz
from pprint import pprint
import random
import requests
import time

START_DATE = '-10s'
END_DATE = '-1s'

SERVER = 'production'
if SERVER == 'development':
    dashboard_url = 'http://localhost:9000/dashboard/v1'
    mobile_url = 'http://localhost:9001/mobile/v1'
    username = 'changeme@itinerum.ca'
    password = 'changeme'
    survey_name = 'changeme'
# Other server configs may be added here
# ---------------------------------------



fake = Factory.create()
uuid_pool = {}
tz = pytz.timezone('America/Montreal')


def admin_login():
    auth_url = dashboard_url + '/auth'

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    body = {
        'email': username,
        'password': password
    }

    response = requests.post(auth_url, headers=headers, json=body)
    token = response.json()['accessToken']
    return token


def admin_get_existing_uuids(token, survey=None):
    uuid_url = dashboard_url + '/itinerum/users/'

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + token
    }

    response = requests.get(uuid_url, headers=headers)
    if response.status_code != 200:
        raise Exception(response)
    uuids = response.json()['results']
    return uuids


def admin_init_uuid_pool():
    print('Getting existing information on server...')
    token = admin_login()
    users = admin_get_existing_uuids(token)

    for user in users:
        uuid_pool[user['uuid']] = user['created_at']
    # print('UUID pool: {}'.format(uuid_pool.keys()))
    return uuid_pool


# submits first request a phone participant would make,
# supplies a survey name and language--receives all survey and
# prompts data in return
def generate_installation(uuid_pool):
    fake_uuid = fake.uuid4()
    while fake_uuid in uuid_pool:
        fake_uuid = fake.uuid4()
    # fake_uuid = random.choice(uuid_pool.keys())

    fake_dt = tz.localize(fake.date_time_between(start_date=START_DATE, end_date=END_DATE)).isoformat()

    # generate fake data
    test_data = {
        'user': {
            'uuid': fake_uuid,
            'model': 'iPhone 4s',
            'itinerumVersion': '99c',
            'os': 'ios' if fake.pybool() else 'android',
            'osVersion': str(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
            'createdAt': fake_dt
        },
        'surveyName': survey_name
    }

    new_installation_url = mobile_url + '/create'
    r = requests.post(new_installation_url, json=test_data)
    assert r.status_code == 201
    response = r.json()['results']

    assert 'survey' in response
    pprint(response)
    assert len(response['survey']) > 0
    assert 'defaultAvatar' in response
    assert '/assets/' in response['defaultAvatar']
    assert 'lang' in response
    assert 'aboutText' in response

    # print('Initial request:')
    # print(json.dumps(test_data, indent=4))
    # print('Response:')
    # print(json.dumps(response, indent=4))
    # print('\n\n-------------------------------\n')
    return fake_uuid, response


def generate_survey_answers(uuid, survey_name, schema):
    def choose_selection(question):
        choice = random.choice(question['fields']['choices'])
        return [choice]
    def choose_selections(question):
        choices = question['fields']['choices']
        num_of_selections = random.randint(0, len(choices))
        selections = set()
        for i in range(num_of_selections):
            selections.add(random.choice(choices))
        return list(selections)
    def choose_number(question):
        return fake.pyint()
    def choose_address(question):
        latitude = str(fake.latitude())
        longitude = str(fake.longitude())
        return { 'latitude': latitude, 'longitude': longitude }
    def choose_email(question):
        return fake.email()
    def choose_text(question):
        return fake.text()
    def skip(question):
        return
    def choose_boolean(question):
        return random.choice([True, False])

    fn = {
        1: choose_selection,
        2: choose_selections,
        3: choose_number,
        4: choose_address,
        5: choose_text,
        98: choose_boolean,     # tos
        99: skip,               # page break
        100: choose_selection,
        101: choose_selection,
        102: choose_selection,
        103: choose_email,
        104: choose_selection,
        105: choose_address,
        106: choose_address,
        107: choose_address,
        108: choose_selection,
        109: choose_selection,
        110: choose_selection,
        111: choose_selection
    }

    test_data = {
        'uuid': uuid,
        'survey': {},
    }

    # answer user supplied questions
    if survey_name in ['kyle', 'itinerummtlte2018', 'itinerummtltf2018', 'itinerummtlte2018ios', 'itinerummtltf2018ios']:
        # itinerummtl2018 has removed "both student and worker" option
        user_type = random.choice(['student', 'worker'])
        if user_type is 'student':
            ignore_ids = [107, 110, 111]
        elif user_type is 'worker':
            ignore_ids = [106, 108, 109]

        for question in schema:
            question_id = question['id']
            if question_id in ignore_ids:
                continue

            col_name = question['colName']

            # handle new mode categories
            itinerummtl_2018_member_types = ['A full-time worker', 'A part-time worker', 'A student',
                                           'Retired', 'At home', 'Other']
            itinerummtl_2018_primary_modes = ['Car / Motorcyle', 'Electric Car (green lic. plate)',
                                            'Bus', 'Metro', 'Train', 'On foot', 'Bicycle', 'Other']
            itinerummtl_2018_secondary_modes = ['No', 'Car / Motorcyle', 'Electric Car (green lic. plate)',
                                              'Bus', 'Metro', 'Train', 'On foot', 'Bicycle', 'Other']

            if col_name == 'member_type':
                test_data['survey'][col_name] = [str(random.randint(0, len(itinerummtl_2018_member_types) - 1))]
            elif col_name in ['travel_mode_work', 'travel_mode_study', 'travel_mode_alt_work', 'travel_mode_alt_study']:
                if col_name in ['travel_mode_work', 'travel_mode_study']:
                    modes = itinerummtl_2018_primary_modes
                else:
                    modes = itinerummtl_2018_secondary_modes
                question = {'fields': {'choices': modes}}
                mode_selections = choose_selections(question)
                mode_selections_idxs = [str(modes.index(s)) for s in mode_selections]
                test_data['survey'][col_name] = mode_selections_idxs
            else:
                col_name = question['colName']
                test_data['survey'][col_name] = fn[question_id](question)

    # handle surveys with default hardcoded questions generally
    else:
        user_type = random.choice(['student', 'worker', 'both'])
        if user_type is 'student':
            ignore_ids = [107, 110, 111]
        elif user_type is 'worker':
            ignore_ids = [106, 108, 109]
        else:
            ignore_ids = []

        for question in schema:
            question_id = question['id']
            if question_id in ignore_ids:
                continue

            col_name = question['colName']
            test_data['survey'][col_name] = fn[question_id](question)

    update_url = mobile_url + '/update'

    r = requests.post(update_url, json=test_data)
    assert r.status_code == 201
    assert r.json()['status'].startswith('Warning (deprecated)')

    # print('Update survey responses request:')
    # print(json.dumps(test_data, indent=4))
    # print('Response:')
    # print(json.dumps(r.json(), indent=4))
    # print('\n\n-------------------------------\n')
    return r


def generate_coordinates(uuid, n=0):
    coordinates = []

    fake_dt = tz.localize(fake.date_time_between(start_date=START_DATE, end_date=END_DATE))
    for i in range(n):
        coordinates.append({
            'latitude': str(45.45 + random.random()/10),
            'longitude': str(-73.55 - random.random()/10),
            'speed': random.uniform(0, 60),
            'vAccuracy': random.randint(0, 35),
            'hAccuracy': random.randint(0, 35),
            'accelerationX': random.random(),
            'accelerationY': random.random(),
            'accelerationZ': random.random(),
            'modeDetected': random.randint(1, 5),
            'pointType': random.randint(1, 8),
            'timestamp': fake_dt.isoformat()
        })
        fake_dt += timedelta(seconds=15)

    # submit coordinates to server
    test_data = {
        'uuid': uuid,
        'coordinates': coordinates,
        'prompts': []
    }

    update_url = mobile_url + '/update'
    r = requests.post(update_url, json=test_data)
    assert r.status_code == 201

    # print('Update coordinates request:')
    # print(json.dumps(test_data, indent=4))
    # print('Response:')
    # print(json.dumps(r.json(), indent=4))
    # print('\n\n-------------------------------\n')
    return r


def generate_cancelled_prompts(uuid, prompts, n=0):
    # do not generate cancelled prompts for surveys without prompts
    if not prompts:
        return

    cancelled_prompts = []
    for i in range(n):
        fake_dt = fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
        c = {
            'uuid': fake.uuid4(),
            'latitude': str(45.45 + random.random()/10),
            'longitude': str(-73.55 + random.random()/10),
            'displayedAt': tz.localize(fake_dt).isoformat(),
            'cancelledAt': None,
            'isTravelling': None,
        }

        # ignored -- no cancelled at, no in_transit
        cancelled_prompt_answered = fake.pybool()
        if cancelled_prompt_answered is True:
            c['cancelledAt'] = tz.localize(fake_dt).isoformat()

            # swipe right to answer secondary cancelled info (cancelled_at, in_transit set to true or false)
            # swift left for 'clear' (cancelled_at, but no in_transit)
            swiped_right = fake.pybool()
            if swiped_right is True:
                c['isTravelling'] = fake.pybool()

        cancelled_prompts.append(c)

    test_data = {
        'uuid': uuid,
        'cancelledPrompts': cancelled_prompts
    }
    cancelled_prompt_url = mobile_url + '/update'
    r = requests.post(cancelled_prompt_url, json=test_data)

    if cancelled_prompts:
        assert r.status_code == 201
    return cancelled_prompts


def generate_prompts_answers(uuid, prompts, cancelled_prompts, n=0):
    def choose_selection(question):
        choice = [random.choice(question['choices'])]
        return choice
    def choose_selections(question):
        choices = question['choices']
        num_of_selections = random.randint(0, len(choices))
        selections = []
        for i in range(num_of_selections):
            selections.append(random.choice(choices))
        return selections
    def choose_text_csv(question):
        return fake.text().split()[:3]
    def choose_text(question):
        return fake.text()

    fn = {
        1: choose_selection,
        2: choose_selections,
        3: choose_text_csv,
        5: choose_text
    }
    answers = []
    for i in range(n):
        # update half of the cancelled prompts to answered prompts
        update_cancelled_prompt = fake.pybool()
        recorded_at_offset = random.randint(0, 180)
        if update_cancelled_prompt is True and cancelled_prompts:
            cancelled_idx = random.randint(0, len(cancelled_prompts) - 1)
            cancelled = cancelled_prompts.pop(cancelled_idx)
            prompt_uuid = cancelled['uuid']
            prompt_displayed_at = cancelled['displayedAt']
            prompt_recorded_at = (dateutil.parser.parse(prompt_displayed_at) + \
                                  timedelta(seconds=recorded_at_offset)).isoformat()
        else:
            prompt_uuid = fake.uuid4()
            fake_dt = fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
            prompt_displayed_at = tz.localize(fake_dt).isoformat()
            prompt_recorded_at = tz.localize(fake_dt + timedelta(seconds=recorded_at_offset)).isoformat()

        prompt_lat = str(45.45 + random.random() / 10)
        prompt_lng = str(-73.55 - random.random() / 10)
        for prompt_idx, prompt in enumerate(prompts):
            answers.append({
                'prompt': prompt['prompt'],
                'uuid': prompt_uuid,
                'prompt_num': prompt_idx,
                'answer': fn[prompt['id']](prompt),
                'displayedAt': prompt_displayed_at,
                'recordedAt': prompt_recorded_at,
                'latitude': prompt_lat,
                'longitude': prompt_lng
            })

    test_data = {
        'uuid': uuid,
        'coordinates': [],
        'prompts': answers
    }

    update_url = mobile_url + '/update'
    r = requests.post(update_url, json=test_data)
    if answers:
        assert r.status_code == 201

    # print('Update prompts request:')
    # print(json.dumps(test_data, indent=4))
    # print('Response:')
    # print(json.dumps(r.json(), indent=4))
    # print('\n\n-------------------------------\n')
    return r


def download_points():
    token = admin_login()
    update_url = dashboard_url + '/data/download/coordinates'
    jwt = 'JWT ' + token
    requests.post(update_url, data={'token': jwt})


def run_test(users=1, points=25):
    uuid_pool = admin_init_uuid_pool()
    times = {
        'generate_installation': [],
        'generate_survey_answers': [],
        'generate_coordinates': [],
        'generate_prompts_answers': [],
        'generate_cancelled_prompts': []
    }

    for i in range(users):
        # step 1: user has installed itinerum and supplied a survey name
        t0 = time.time()
        uuid, response = generate_installation(uuid_pool)

        # step 2: user has answered survey questions and is ready to begin collecting points
        t1 = time.time()
        survey_name = response['surveyName']
        generate_survey_answers(uuid, survey_name, response['survey'])

        # step 3: add coordinates
        t2 = time.time()
        generate_coordinates(uuid, n=points)
        # generate_coordinates(uuid, 0, n=points, real_points=real_points)

        # step 4: add cancelled prompts (if prompts exist)
        t3 = time.time()
        cancelled = generate_cancelled_prompts(uuid,
                                               prompts=response['prompt']['prompts'],
                                               n=8)

        # step 5: add prompt answers (if prompts exist)
        t4 = time.time()
        generate_prompts_answers(uuid,
                                 prompts=response['prompt']['prompts'],
                                 cancelled_prompts=cancelled,
                                 n=3)

        t5 = time.time()

        times['generate_installation'].append(t1-t0)
        times['generate_survey_answers'].append(t2-t1)
        times['generate_coordinates'].append(t3-t2)
        times['generate_prompts_answers'].append(t4-t3)
        times['generate_cancelled_prompts'].append(t5-t4)

        if (i + 1) % 5 == 0:
            print('#{i}: {time}s - {uuid}'.format(i=i+1, time=t4-t0, uuid=uuid))

    def avg(times):
        return sum(times) / len(times)

    print('Avg installation time:', avg(times['generate_installation']))
    print('Avg survey time:', avg(times['generate_survey_answers']))
    print('Avg coordinates time:', avg(times['generate_coordinates']))
    print('Avg mode prompts time:', avg(times['generate_prompts_answers']))
    print('Avg cancelled prompts time', avg(times['generate_cancelled_prompts']))

    all_times = sum([avg(v) for k, v in times.items()])
    print('Avg total time:', all_times)


if __name__ == '__main__':
    # download_points()
    run_test(users=1, points=25)
