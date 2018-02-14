#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
from flask_restful import Resource

from mobile.database import Database
from utils.responses import Success, Error
from utils.validators import validate_json, value_exists

database = Database()


class MobileUpdateDataRoute(Resource):
    headers = {'Location': '/update'}
    resource_type = 'MobileUpdateData'

    # this route is modelled off the legacy PHP mobile api, API v2 should
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
                survey_answers = database.survey.upsert(user=user,
                                                        answers=validated['survey_answers'])
                if survey_answers:
                    response['survey'] = 'Survey answer for {} upserted.'.format(user.uuid)
            if validated['coordinates']:
                coordinates = database.coordinates.insert(user=user,
                                                          coordinates=validated['coordinates'])
                if coordinates:
                    response['coordinates'] = (
                        'New coordinates for {} inserted.'.format(user.uuid))
            
            # upsert prompts answers and remove any existing conflicting cancelled prompt responses
            if validated['prompts_answers']:
                prompts_answers = database.prompts.upsert(user=user,
                                                          prompts=validated['prompts_answers'])
                prompts_uuids = [p.prompt_uuid for p in prompts_answers]
                database.cancelled_prompts.delete(prompts_uuids)

                if prompts_answers:
                    response['prompts'] = (
                        'New prompt answers for {} inserted.'.format(user.uuid))

            # filter cancelled prompts which conflict with a provided response by uuid and insert cancelled prompts
            if validated['cancelled_prompts']:
                if validated['prompts_answers']:
                    answers_uuids = {p['uuid'] for p in validated['prompts_answers']}
                    filtered_cancelled_prompts = []
                    for c in validated['cancelled_prompts']:
                        if c['uuid'] not in answers_uuids:
                            filtered_cancelled_prompts.append(c)
                else:
                    filtered_cancelled_prompts = validated['cancelled_prompts']
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

            return Success(status_code=status,
                           headers=self.headers,
                           resource_type=self.resource_type,
                           body=response)

        return Error(status_code=400,
                     headers=self.headers,
                     resource_type=self.resource_type,
                     errors=['Could not find survey for {}.'.format(validated['uuid'])])
