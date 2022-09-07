#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017
from models import (db, PromptQuestion, Survey, SurveyQuestion, SurveyResponse)

from hardcoded_survey_questions import lookup, default_stack

DEFAULT_STACK_COLUMNS = [q['colName'] for q in default_stack]


class MobileSurveyActions:
    @staticmethod
    def _map_hardcoded_ints(survey, column, answer):
        # Intercept Itinerum MTL 2018 and map their updated hardcoded modes.
        # TO DO: Remove this when hardcoded questions removed from platform.
        if survey.name in ['itinerummtlte2018', 'itinerummtltf2018', 'itinerummtlte2018ios', 'itinerummtltf2018ios', 'itinerummtlte2018cm', 'itinerummtltf2018cm']:
            en_occupations = [
                'A full-time worker',
                'A part-time worker',
                'A student',
                'Retired',
                'At home',
                'Other'
            ]
            fr_occupations = [
                'Travailleur à plein temps',
                'Travailleur à temps partiel',
                'Étudiant',
                'Retraité',
                'À la maison',
                'Autre'
            ]
            en_modes = [
                'Car / Motorcyle',
                'Electric Car (green lic. plate)',
                'Bus',
                'Metro',
                'Train',
                'On foot',
                'Bicycle',
                'Other'
            ]
            fr_modes = [
                'Auto / Moto',
                'Auto électrique (plaque vert)',
                'Bus',
                'Métro',
                'Train',
                'À pied',
                'Vélo',
                'Autre'
            ]

            choices = None
            if column == 'member_type':
                if survey.language == 'en':
                    choices = en_occupations
                elif survey.language == 'fr':
                    choices = fr_occupations
                return choices[int(answer)]
            elif column in ['travel_mode_work', 'travel_mode_study']:
                if survey.language == 'en':
                    choices = en_modes
                elif survey.language == 'fr':
                    choices = fr_modes
                # make sure answer is supplied as an iterable                
                if not isinstance(answer, list):
                    answer = [answer]
                selected_modes = []
                for choice_idx_str in answer:
                    text_answer = choices[int(choice_idx_str)]
                    selected_modes.append(text_answer)
                return selected_modes
            elif column in ['travel_mode_alt_work', 'travel_mode_alt_study']:
                if survey.language == 'en':
                    choices = ['No'] + en_modes
                elif survey.language == 'fr':
                    choices = ['Non'] + fr_modes
                # make sure answer is supplied as an iterable                
                if not isinstance(answer, list):
                    answer = [answer]
                selected_modes = []
                for choice_idx_str in answer:
                    text_answer = choices[int(choice_idx_str)]
                    selected_modes.append(text_answer)
                return selected_modes
            elif column in DEFAULT_STACK_COLUMNS:
                index = DEFAULT_STACK_COLUMNS.index(column)
                if survey.language == 'en':
                    choices = default_stack[index]['fields'].get('choices')
                else:
                    choices = default_stack[index]['fields'].get('choices_fr')
                if choices:
                    return choices[int(answer)]            
            return answer

        # handle all other surveys as normal
        if column in DEFAULT_STACK_COLUMNS:
            index = DEFAULT_STACK_COLUMNS.index(column)
            if survey.language == 'en':
                choices = default_stack[index]['fields'].get('choices')
            else:
                choices = default_stack[index]['fields'].get('choices_fr')
            if choices:
                return choices[int(answer)]
        return answer

    def get(self, survey_id):
        return Survey.query.get(survey_id)

    def find_by_name(self, name):
        return Survey.query.filter(Survey.name.ilike(name)).one_or_none()

    def upsert(self, user, answers):
        survey = user.survey
        for column, answer in answers.items():
            # handle singular list responses--this conflicts with the sepcial
            # case handling for itinerumMTL 2018. This is reverted by the special case
            # function and should be handled better.
            if isinstance(answer, list) and len(answer) == 1:
                answer = answer[0]
            text_answer = self._map_hardcoded_ints(survey, column, answer)
            answers[column] = text_answer
        if user.survey_response.one_or_none():
            response = user.survey_response
            response.answers = answers
        else:
            response = SurveyResponse(
                survey_id=survey.id,
                mobile_id=user.id,
                response=answers)
            db.session.add(response)
        db.session.commit()
        return response

    def formatted_survey_questions(self, survey):
        survey_json = []
        for question in survey.survey_questions.order_by(SurveyQuestion.question_num):
            json_question = {
                'id': question.question_type,
                'colName': question.question_label,
                'prompt': question.question_text,
                'fields': {},
                'answerRequired': question.answer_required
            }

            json_field_type = lookup[question.question_type]

            if json_field_type:
                if len(json_field_type) == 1:
                    json_question['fields']['choices'] = []

                    # do not provide empty string choices (email)
                    if len(question.choices) == 1 and not question.choices[0].choice_text.strip():
                        pass
                    else:
                        for choice in question.choices:
                            json_question['fields']['choices'].append(choice.choice_text)
                else:
                    json_question['fields'] = dict.fromkeys(json_field_type)
            survey_json.append(json_question)
        return survey_json

    def formatted_survey_prompts(self, survey):
        prompts_json = []
        for prompt in survey.prompt_questions.order_by(PromptQuestion.prompt_num):
            json_prompt = {
                'id': prompt.prompt_type,
                'colName': prompt.prompt_label,
                'prompt': prompt.prompt_text,
                'choices': [],
                'answerRequired': prompt.answer_required
            }

            for choice in prompt.choices:
                json_prompt['choices'].append(choice.choice_text)

            prompts_json.append(json_prompt)
        return prompts_json
