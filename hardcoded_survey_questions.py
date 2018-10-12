#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2016-2018
#
# Note: Mandatory questions hardcoded for beginning of survey
#       to eventually be removed entirely. Optional components
#       for each should be made in their place and left to the
#       survey administrator's discretion.


# field names and concatenation order for survey responses
lookup = {
    1: ['choices'],                     # Select one
    2: ['choices'],                     # Select many
    3: ['number'],                      # Number input
    4: ['latitude', 'longitude'],       # Map/Address
    5: ['text'],                        # Text Box
    98: ['text'],                       # Terms of Service
    99: [],                             # Page break
    100: ['gender'],                    # Hardcoded: Gender
    101: ['age'],                       # Hardcoded: Age
    102: ['choices'],                   # Hardcoded: Primary Mode
    103: ['email'],                     # Hardcoded: Email
    104: ['choices'],                   # Hardcoded: member_type (primary occupation)
    105: ['latitude', 'longitude'],     # Hardcoded: home_location
    106: ['latitude', 'longitude'],     # Hardcoded: study_location
    107: ['latitude', 'longitude'],     # Hardcoded: work_location
    108: ['choices'],                   # Hardcoded: travel_mode_study
    109: ['choices'],                   # Hardcoded: travel_mode_alt_study
    110: ['choices'],                   # Hardcoded: travel_mode_work
    111: ['choices']                    # Hardcoded: travel_mode_alt_work
}

# the default questions to populate each new survey with
default_stack = [
    {
        "prompt": "Please enter your home location on the map",
        "id": 105,
        "fields": {
            "latitude": None,
            "latitude": None,
        },
        "colName": "location_home",
        "answerRequired": True
    },
    {
        "prompt": "What is your primary occupation?",
        "id": 104,
        "fields": {
            "choices": [
                "A full-time worker",
                "A part-time worker",
                "A student",
                "A student and a worker",
                "Retired",
                "At home",
                "Other"
            ],
            "choices_fr": [
                "Travailleur à plein temps",
                "Travailleur à temps partiel",
                "Étudiant",
                "Étudiant et travailleur",
                "Retraité",
                "À la maison",
                "Autre"
            ]
        },
        "colName": "member_type",
        "answerRequired": True
    },
    {
        "prompt": "Please enter your work location on the map",
        "id": 107,
        "fields": {
            "latitude": None,
            "latitude": None,
        },
        "colName": "location_work",
        "answerRequired": True
    },
    {
        "prompt": "How do you typically commute to your work location?",
        "id": 110,
        "fields": {
            "choices": [
                "Walk",
                "Bicycle",
                "Public Transit",
                "Car",
                "Car & Public Transit",
                "Other Mode",
                "Other Combinations"
            ],
            "choices_fr": [
                "À pied",
                "Vélo",
                "Transport Collectif",
                "Voiture",
                "Voiture & Transport Collectif",
                "Autre mode unique",
                "Autre combinaison"
            ]
        },
        "colName": "travel_mode_work",
        "answerRequired": True
    },
    {
        "prompt": "Do you use any alternative mode of travel to work?",
        "id": 111,
        "fields": {
            "choices": [
                "N/A",
                "Walk",
                "Bicycle",
                "Public Transit",
                "Car",
                "Car & Public Transit",
                "Other Mode",
                "Other Combinations"
            ],
            "choices_fr": [
                "N/A",
                "À pied",
                "Vélo",
                "Transport Collectif",
                "Voiture",
                "Voiture & Transport Collectif",
                "Autre mode unique",
                "Autre combinaison"
            ]
        },
        "colName": "travel_mode_alt_work",
        "answerRequired": True
    },
    {
        "prompt": "Please enter your study location on the map",
        "id": 106,
        "fields": {
            "latitude": None,
            "latitude": None,
        },
        "colName": "location_study",
        "answerRequired": True
    },
    {
        "prompt": "How do you typically commute to your studies?",
        "id": 108,
        "fields": {
            "choices": [
                "Walk",
                "Bicycle",
                "Public Transit",
                "Car",
                "Car & Public Transit",
                "Other Mode",
                "Other Combinations"
            ],
            "choices_fr": [
                "À pied",
                "Vélo",
                "Transport Collectif",
                "Voiture",
                "Voiture & Transport Collectif",
                "Autre mode unique",
                "Autre combinaison"
            ]
        },
        "colName": "travel_mode_study",
        "answerRequired": True
    },
    {
        "prompt": "Do you use any alternative mode of travel to your studies?",
        "id": 109,
        "fields": {
            "choices": [
                "N/A",
                "Walk",
                "Bicycle",
                "Public Transit",
                "Car",
                "Car & Public Transit",
                "Other Mode",
                "Other Combinations"
            ],
            "choices_fr": [
                "N/A",
                "À pied",
                "Vélo",
                "Transport Collectif",
                "Voiture",
                "Voiture & Transport Collectif",
                "Autre mode unique",
                "Autre combinaison"
            ]
        },
        "colName": "travel_mode_alt_study",
        "answerRequired": True
    },
    {
        "prompt": "What is your gender?",
        "id": 100,
        "fields": {
            "choices": [
                "Male",
                "Female",
                "Other/Neither",
                "Does not wish to respond"
            ],
            "choices_fr": [
                "Homme",
                "Femme",
                "Autre / aucune de ces réponses",
                "Ne veut pas répondre"
            ]
        },
        "colName": "Gender",
        "answerRequired": True
    },
    {
        "prompt": "What is your age bracket?",
        "id": 101,
        "fields": {
            "choices": [
                "16-24",
                "25-34",
                "35-44",
                "45-54",
                "55-64",
                "65-74",
                "75-84",
                "85+"
            ],
            "choices_fr": [
                "16-24",
                "25-34",
                "35-44",
                "45-54",
                "55-64",
                "65-74",
                "75-84",
                "85+"
            ]
        },
        "colName": "Age",
        "answerRequired": True
    },
    {
        "prompt": "Please enter your email",
        "id": 103,
        "fields": {
            "email": ""
        },
        "colName": "Email",
        "answerRequired": True
    },
]
