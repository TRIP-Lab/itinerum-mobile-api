#!/usr/bin/env python
# Kyle Fitzsimmons, 2017-2018
#
# Utils: generic data structure helper functions
import hardcoded_survey_questions
import re


def cast(value, _type):
    try:
        return _type(value)
    except TypeError:
        return None


def to_english(survey, word, question_label):
    key = 'choices'
    if survey.language != 'en':
        key = 'choices_{lang}'.format(lang=survey.language)
    question = [q for q in hardcoded_survey_questions.default_stack
                if q['colName'] == question_label]
    if question:
        question = question[0]
        word = word.encode('utf-8')
        idx = [choice.lower() for choice in question['fields'][key]].index(word)
        return question['fields']['choices'][idx].lower()


# http://stackoverflow.com/a/6027615/6073881
def flatten_dict(value_dict, parent_key='', sep='.'):
    items = []
    for key, value in value_dict.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


_camelcase_pattern = re.compile(r'([A-Z])')
def camelcase_to_underscore(name):
    return _camelcase_pattern.sub(lambda x: '_' + x.group(1).lower(), name)

_underscore_pattern = re.compile(r'_([a-z])')
def underscore_to_camelcase(name):
    return _underscore_pattern.sub(lambda x: x.group(1).upper(), name)


def rename_json_keys(d, convert_func):
    renamed = None
    if isinstance(d, dict):
        new_d = {}
        for key, value in d.items():
            new_d[convert_func(key)] = rename_json_keys(value, convert_func) if isinstance(value, dict) else value
        renamed = new_d
    elif isinstance(d, list):
        new_l = []
        for value in d:
            new_l.append(rename_json_keys(value, convert_func) if isinstance(value, dict) else value)
        renamed = new_l
    return renamed


# https://www.python.org/dev/peps/pep-0485/#proposed-implementation
# An implementation of Python 3.5's std library's math.isclose() function
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    a, b = float(a), float(b)
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
