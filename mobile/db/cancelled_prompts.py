#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017
import ciso8601
from sqlalchemy.exc import IntegrityError

from models import db, CancelledPromptResponse


class MobileCancelledPromptsActions:
    def get(self, prompts_uuids):
        uuid_filters = CancelledPromptResponse.prompt_uuid.in_(prompts_uuids)
        return db.session.query(CancelledPromptResponse).filter(uuid_filters)        

    def insert(self, user, cancelled_prompts):
        bulk_rows = []
        for prompt in cancelled_prompts:
            cancelled_at = prompt.get('cancelled_at')
            if cancelled_at:
                cancelled_at = ciso8601.parse_datetime(cancelled_at)

            c = CancelledPromptResponse(survey_id=user.survey.id,
                                        mobile_id=user.id,
                                        prompt_uuid=prompt['uuid'],
                                        latitude=prompt['latitude'],
                                        longitude=prompt['longitude'],
                                        displayed_at=ciso8601.parse_datetime(prompt['displayed_at']),
                                        cancelled_at=cancelled_at,
                                        is_travelling=prompt.get('is_travelling'))
            bulk_rows.append(c)
        try:
            db.session.bulk_save_objects(bulk_rows)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return cancelled_prompts

    def delete(self, prompts_uuids):
        to_delete = self.get(prompts_uuids)
        for prompt in to_delete:
            db.session.delete(prompt)
        db.session.commit()
