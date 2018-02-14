#!/usr/bin/env python
# Kyle Fitzsimmons, 2017-2018
#
# Utils: generic data structure helper functions
import hardcoded_survey_questions


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


def make_keys_camelcase(dicts, max_depth=5):
    def _recursive_camelcase(d, depth=0):
        if depth + 1 == max_depth:
            return d

        output = {}
        for key, value in d.items():
            new_key = ''.join(letter.capitalize() or '_' for letter in key.split('_'))
            new_key = new_key[0].lower() + new_key[1:]

            # continue into next level if value is a dictionary
            if isinstance(value, dict):
                next_level = depth + 1
                output[new_key] = _recursive_camelcase(value, depth=next_level)
            else:
                output[new_key] = d[key]

        return output

    return_one = isinstance(dicts, dict)
    if return_one:
        dicts = (dicts,)
    camelcase_dicts = [_recursive_camelcase(d) for d in dicts]
    if return_one:
        camelcase_dicts = camelcase_dicts[0]
    return camelcase_dicts
