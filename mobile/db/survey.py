#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017
from models import (db, PromptQuestion, Survey, SurveyQuestion, SurveyResponse)

from hardcoded_survey_questions import lookup, default_stack

DEFAULT_STACK_COLUMNS = [q['colName'] for q in default_stack]


class MobileSurveyActions:
    @staticmethod
    def _map_hardcoded_ints(language, column, answer):
        if column in DEFAULT_STACK_COLUMNS:
            index = DEFAULT_STACK_COLUMNS.index(column)
            if language == 'en':
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
            # handle singular list responses
            if isinstance(answer, list) and len(answer) == 1:
                answer = answer[0]
            text_answer = self._map_hardcoded_ints(survey.language, column, answer)
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
                'fields': {}
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
                'choices': []
            }

            for choice in prompt.choices:
                json_prompt['choices'].append(choice.choice_text)

            prompts_json.append(json_prompt)
        return prompts_json
