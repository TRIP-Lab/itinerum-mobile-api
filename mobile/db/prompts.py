#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017
from datetime import datetime
import pytz

from models import db, PromptResponse


class MobilePromptsActions:

    def get(self, prompts_uuids):
        prompts_filters = PromptResponse.prompt_uuid.in_(prompts_uuids)
        return db.session.query(PromptResponse).filter(prompts_filters)


    # formats a prompts query to a lookup dictionary
    # [p0, p1, p2] --> {p0_uuid: {p0_prompt_num: p0}, ...}
    def create_lookup(self, prompts):
        prompts_lookup = {}
        for p in prompts:
            prompts_lookup.setdefault(p.prompt_uuid, {})
            prompts_lookup[p.prompt_uuid][p.prompt_num] = p
        return prompts_lookup

    def upsert(self, user, prompts):
        prompts_uuids = {p['uuid'] for p in prompts}
        existing_prompts = self.get(prompts_uuids)
        existing_lookup = self.create_lookup(existing_prompts)

        responses = []
        for prompt in prompts:
            # gracefully handle change of 'timestamp' -> 'displayed_at'
            if 'timestamp' in prompt:
                prompt['displayed_at'] = prompt.pop('timestamp')

            uuid = prompt['uuid']
            prompt_num = int(prompt['prompt_num'])
            if uuid in existing_lookup:
                response = existing_lookup[uuid][prompt_num]
                response.response = prompt['answer']
                response.recorded_at = prompt['recorded_at']
                response.latitude = prompt['latitude']
                response.longitude = prompt['longitude']
                response.edited_at = datetime.now(pytz.utc)
            else:
                response = PromptResponse(
                    survey_id=user.survey_id,
                    mobile_id=user.id,
                    prompt_uuid=uuid,
                    prompt_num=prompt_num,
                    response=prompt['answer'],
                    displayed_at=prompt['displayed_at'],
                    recorded_at=prompt['recorded_at'],
                    latitude=prompt['latitude'],
                    longitude=prompt['longitude'])
            responses.append(response)
        db.session.bulk_save_objects(responses)
        db.session.commit()
        return responses
