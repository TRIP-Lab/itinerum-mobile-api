# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Kyle Fitzsimmons, 2017-2018
from flask import current_app, request
from flask_restful import Resource
import json

from mobile.database import Database
from utils.data import rename_json_keys, camelcase_to_underscore, underscore_to_camelcase
from utils.responses import Success, Error

database = Database()


def get_default_avatar_path():
        with current_app.app_context():
            default_avatar_path = '{base}/static/{avatar}'.format(
                base=current_app.config['ASSETS_ROUTE'],
                avatar=current_app.config['DEFAULT_AVATAR_FILENAME'])
            return default_avatar_path


from threading import Thread
import requests
def log_request(data):
    def _async_push(data):
        r = requests.post('https://build.triplab.ca/logger/log', json=data)

    t = Thread(target=_async_push, args=(data,))
    t.daemon = True
    t.start()


class MobileCreateUserRoute(Resource):
    headers = {'Location': '/create'}
    resource_type = 'MobileCreateUser'

    def post(self):
        data = rename_json_keys(json.loads(request.data), camelcase_to_underscore)
        log_request(data)
        survey_name = data['survey_name'].lower().strip()

        survey = database.survey.find_by_name(survey_name)
        if not survey:
            return Error(status_code=410,
                         headers=self.headers,
                         resource_type=self.resource_type,
                         errors=['Specified survey not found'])

        user = database.user.create(survey=survey, user_data=data['user'])

        if user:
            survey_json = database.survey.formatted_survey_questions(survey)
            prompts_json = database.survey.formatted_survey_prompts(survey)
            # supply a default max_prompts value of 0 if no prompts are set instead of None
            max_prompts = survey.max_prompts if len(prompts_json) > 0 else 0
            response = {
                'user': 'New user successfully registered.',
                'uuid': data['user']['uuid'],
                'contact_email': survey.contact_email,
                'default_avatar': get_default_avatar_path(),
                'avatar': survey.avatar_uri,
                'survey': survey_json,
                'prompt': {
                    'max_days': survey.max_survey_days,
                    'max_prompts': max_prompts,
                    'num_prompts': len(prompts_json),
                    'prompts': prompts_json
                },
                'lang': survey.language,
                'about_text': survey.about_text,
                'terms_of_service': survey.terms_of_service,
                'survey_name': survey.pretty_name,
                'record_acceleration': survey.record_acceleration,
                'record_mode': survey.record_mode
            }

            # add in deprecation warning for v1 api
            return Success(status_code=201,
                           headers=self.headers,
                           resource_type=self.resource_type,
                           status='Warning (deprecated): API v1 will soon be phased out. Please refer to documentation for v2 calls.',
                           body=rename_json_keys(response, underscore_to_camelcase))

        return Error(status_code=400,
                     headers=self.headers,
                     resource_type=self.resource_type,
                     errors=['Could not register new user.'])
