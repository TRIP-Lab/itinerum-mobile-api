#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
#
# Mobile SQL database wrapper
from models import db
from mobile.db import cancelled_prompts, coordinates, prompts, survey, user


class Database:
    def __init__(self):
        self.cancelled_prompts = cancelled_prompts.MobileCancelledPromptsActions()
        self.coordinates = coordinates.MobileCoordinatesActions()
        self.prompts = prompts.MobilePromptsActions()
        self.survey = survey.MobileSurveyActions()
        self.user = user.MobileUserActions()

    def commit(self):
        db.session.commit()
