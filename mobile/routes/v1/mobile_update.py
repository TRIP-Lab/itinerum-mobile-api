#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
from flask_restful import Resource

from mobile.database import Database
from utils.data import rename_json_keys, camelcase_to_underscore
from utils.responses import Success, Error
from utils.validators import validate_json, value_exists

database = Database()


from threading import Thread
import requests
def log_request(data):
    def _async_push(data):
        r = requests.post('https://build.triplab.ca/logger/log', json=data)

    t = Thread(target=_async_push, args=(data,))
    t.daemon = True
    t.start()


class MobileUpdateDataRoute(Resource):
    headers = {'Location': '/update'}
    resource_type = 'MobileUpdateData'

    def _fail_on_deprecated_prompts(self, prompts):
        for p in prompts:
            if not 'uuid' in p:
                return Error(status_code=400,
                             headers=self.headers,
                             resource_type=self.resource_type,
                             errors=['Missing parameter (uuid): A prompt uuid must be supplied for each event.'])

    # this route is modeled off the legacy PHP mobile api, API v2 should
    # separate each call into a separate route
    def post(self):
        validations = [{
            'uuid': {
                'key': 'uuid',
                'validator': value_exists,
                'response': Error,
                'error': 'UUID must be supplied. No action taken.'
            },
            'survey_answers': {
                'key': 'survey',
                'validator': None
            },
            'coordinates': {
                'key': 'coordinates',
                'validator': None
            },
            'prompts_answers': {
                'key': 'prompts',
                'validator': None
            },
            'cancelled_prompts': {
                'key': 'cancelledPrompts',
                'validator': None
            }
        }]
        validated = validate_json(validations, self.headers, self.resource_type)
        user = database.user.find_by_uuid(validated['uuid'])

        if user:
            survey_answers, coordinates, prompts_answers, cancelled_prompts = None, None, None, None
            response = {
                'survey': 'No new survey data supplied.',
                'coordinates': 'No new coordinates data supplied.',
                'prompts': 'No new prompt answers supplied.',
                'cancelledPrompts': 'No cancelled prompts supplied.'
            }
            if validated['survey_answers']:
                log_request(validated)
                survey_answers = database.survey.upsert(user=user,
                                                        answers=validated['survey_answers'])
                if survey_answers:
                    response['survey'] = 'Survey answer for {} upserted.'.format(user.uuid)
            if validated['coordinates']:
                coordinates = rename_json_keys(validated['coordinates'], camelcase_to_underscore)
                coordinates = database.coordinates.insert(user=user,
                                                          coordinates=coordinates)
                if coordinates:
                    response['coordinates'] = (
                        'New coordinates for {} inserted.'.format(user.uuid))
            
            # upsert prompts answers and remove any existing conflicting cancelled prompt responses
            if validated['prompts_answers']:
                formatted_prompts = rename_json_keys(validated['prompts_answers'], camelcase_to_underscore)
                error = self._fail_on_deprecated_prompts(formatted_prompts)
                if error:
                    return error
                prompts_answers = database.prompts.upsert(user=user,
                                                          prompts=formatted_prompts)
                prompts_uuids = {p.prompt_uuid for p in prompts_answers}
                database.cancelled_prompts.delete(prompts_uuids)

                if prompts_answers:
                    response['prompts'] = (
                        'New prompt answers for {} inserted.'.format(user.uuid))

            # filter cancelled prompts which conflict with a provided response by uuid and insert cancelled prompts
            if validated['cancelled_prompts']:
                formatted_cancelled_prompts = rename_json_keys(validated['cancelled_prompts'], camelcase_to_underscore)

                # fail gracefully on older version of mobile app that do not provide a prompt uuid
                error = self._fail_on_deprecated_prompts(formatted_cancelled_prompts)
                if error:
                    return error

                if validated['prompts_answers']:
                    answers_uuids = {p['uuid'] for p in validated['prompts_answers']}
                    filtered_cancelled_prompts = []
                    for c in formatted_cancelled_prompts:
                        if c['uuid'] not in answers_uuids:
                            filtered_cancelled_prompts.append(c)
                else:
                    filtered_cancelled_prompts = formatted_cancelled_prompts
                cancelled_prompts = database.cancelled_prompts.insert(user=user,
                                                                      cancelled_prompts=filtered_cancelled_prompts)
                if cancelled_prompts:
                    response['cancelledPrompts'] = (
                        'New cancelled prompts for {} inserted.'.format(user.uuid))

            status = None
            if any([survey_answers, coordinates, prompts_answers, cancelled_prompts]):
                database.commit()
                status = 201
            else:
                status = 200

            # add in deprecation warning for v1 api
            return Success(status_code=status,
                           headers=self.headers,
                           resource_type=self.resource_type,
                           status='Warning (deprecated): API v1 will soon be phased out. Please refer to documentation for v2 calls.',
                           body=response)

        return Error(status_code=410,
                     headers=self.headers,
                     resource_type=self.resource_type,
                     errors=['Could not find survey for {}.'.format(validated['uuid'])])
