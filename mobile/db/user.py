#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017
import ciso8601
from datetime import datetime
import pytz

from models import db, MobileUser


class MobileUserActions:
    def find_by_uuid(self, uuid):
        return MobileUser.query.filter_by(uuid=uuid).one_or_none()

    def _has_answered_survey(self, user):
        return user.survey_response.one_or_none()

    def create(self, survey, user_data):
        created_at = user_data.get('created_at')
        if created_at:
            created_at = ciso8601.parse_datetime(created_at)
        else:
            created_at = datetime.now(pytz.utc)

        existing = self.find_by_uuid(uuid=user_data['uuid'])
        if not existing:
            user = MobileUser(
                survey_id=survey.id,
                uuid=user_data['uuid'],
                model=user_data['model'],
                itinerum_version=user_data['itinerum_version'],
                os=user_data['os'],
                os_version=user_data['os_version'],
                created_at=created_at
            )
            db.session.add(user)
            db.session.commit()
            return user

        # TODO: disabled for testing but re-enable when we go live!
        # (toggles whether survey answers can be edited via phone)
        # elif existing and not self._has_answered_survey(existing):
        else:
            existing.model = user_data['model']
            existing.itinerum_version = user_data['itinerum_version'],
            existing.os = user_data['os'],
            existing.os_version = user_data['os_version'],
            existing.created_at = created_at
            db.session.add(existing)
            db.session.commit()
            return existing
