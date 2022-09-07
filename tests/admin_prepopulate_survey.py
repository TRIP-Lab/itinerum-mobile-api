#!/usr/bin/env python
# Kyle Fitzsimmons, 2016-2018
#
# Functions to replicate admin dashboard survey creation from
# JSON schema for running unit tests
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password
import json
from models import (PromptQuestion, PromptQuestionChoice,
                    Survey, SurveyResponse, SurveyQuestion, SurveyQuestionChoice,
                    WebUser, WebUserRole)
from tests.hardcoded_survey_questions import default_stack


def read_schema(survey_schema_fn):
    with open(survey_schema_fn, 'r') as schema_f:
        schema = json.loads(schema_f.read())
        return schema


def generate_multicolumn_index(db, survey):
    searchable_field_ids = (1, 2, 3, 5, 6, 100, 101, 102,
                            103, 104, 108, 109, 110, 111)
    query = survey.survey_questions
    answers_columns = [q.question_label for q in query.all()
                       if q.question_type in searchable_field_ids]

    if answers_columns:
        # create a new multi-index for full-text search
        index_fields = []
        for col in answers_columns:
            index_fields.append(db.func.lower(SurveyResponse.response[col].astext))

        new_index = db.Index('survey{}_multi_idx'.format(survey.id), *index_fields)
        new_index.create(bind=db.engine)
        db.session.flush()

def load_survey_questions(db, survey, questions):
        # load hardcoded default questions to new survey
        for question_index, question in enumerate(questions):
            survey_question = SurveyQuestion(
                survey_id=survey.id,
                question_num=question_index,
                question_type=question['id'],
                question_label=question['colName'],
                question_text=question['prompt'])

            for field_name, field_value in question['fields'].items():
                # ignore non-english (default) field names
                if 'choices_' in field_name:
                    continue

                if field_name == 'choices':
                    # use integer (list index) value for hardcoded
                    # question responses instead of text-values (iOS app request);
                    # this has a reciprocal reverse-lookup in the mobile api
                    if question['id'] >= 100:
                        for choice_index, choice_text in enumerate(field_value):
                            question_choice = SurveyQuestionChoice(
                                choice_num=choice_index,
                                choice_text=choice_index,
                                choice_field='option')
                            survey_question.choices.append(question_choice)

                    else:
                        for choice_index, choice_text in enumerate(field_value):
                            question_choice = SurveyQuestionChoice(
                                choice_num=choice_index,
                                choice_text=choice_text,
                                choice_field='option')
                            survey_question.choices.append(question_choice)
                else:
                    question_choice = SurveyQuestionChoice(
                        choice_num=None,
                        choice_text=field_value,
                        choice_field=field_name)
                    survey_question.choices.append(question_choice)
            db.session.add(survey_question)
        db.session.commit()
        generate_multicolumn_index(db, survey)


def load_survey_prompts(db, survey, prompts):
    for prompt_index, prompt in enumerate(prompts):
        prompt_question = PromptQuestion(survey_id=survey.id,
                                         prompt_num=prompt_index,
                                         prompt_type=prompt['id'],
                                         prompt_label=prompt['colName'],
                                         prompt_text=prompt['prompt'])
        for choice_index, choice_text in enumerate(prompt['fields']['choices']):
            question_choice = PromptQuestionChoice(
                prompt_id=prompt_question.id,
                choice_num=choice_index,
                choice_text=choice_text,
                choice_field='option')
            prompt_question.choices.append(question_choice)
        db.session.add(prompt_question)


def create_admin_user(db, survey, email, password):
    user_datastore = SQLAlchemyUserDatastore(db, WebUser, WebUserRole)
    admin_role = user_datastore.find_or_create_role(name='admin')
    user = user_datastore.create_user(
        email=email,
        password=encrypt_password(password),
        survey_id=survey.id)
    user_datastore.add_role_to_user(user, admin_role)


def prepopulate(db, survey_schema_fn):
    survey_schema = read_schema(survey_schema_fn)
    survey_name = survey_schema['surveyName']
    language = survey_schema['language']

    survey = Survey(name=survey_name.lower(),
                    pretty_name=survey_name,
                    language=language)
    db.session.add(survey)
    db.session.commit()

    survey_questions = default_stack + survey_schema['surveyQuestions']
    load_survey_questions(db, survey, survey_questions)
    load_survey_prompts(db, survey, prompts=survey_schema['surveyPrompts'])
    create_admin_user(db, survey, survey_schema['adminEmail'], survey_schema['adminPassword'])
    db.session.commit()

