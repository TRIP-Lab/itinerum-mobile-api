#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017
from models import db, MobileCoordinate
import ciso8601


class MobileCoordinatesActions:
    @staticmethod
    def _chunks(iterable, n):
        it = iter(iterable)
        while True:
            chunk = []
            for i in range(n):
                try:
                    chunk.append(next(it))
                except StopIteration:
                    yield chunk
                    raise StopIteration
            yield chunk

    def insert(self, user, coordinates):
        inserted_coordinates = []
        survey_id, mobile_id = user.survey_id, user.id
        for chunk in self._chunks(coordinates, 5000):
            bulk_rows = []
            for point in chunk:
                coordinate = MobileCoordinate(
                    survey_id=survey_id,
                    mobile_id=mobile_id,
                    latitude=point['latitude'],
                    longitude=point['longitude'],
                    altitude=point.get('altitude'),
                    speed=point.get('speed'),
                    direction=point.get('direction'),
                    h_accuracy=point.get('h_accuracy'),
                    v_accuracy=point.get('v_accuracy'),
                    acceleration_x=point.get('acceleration_x'),
                    acceleration_y=point.get('acceleration_y'),
                    acceleration_z=point.get('acceleration_z'),
                    mode_detected=point.get('mode_detected'),
                    point_type=point.get('point_type'),
                    timestamp=ciso8601.parse_datetime(point['timestamp'])
                )
                bulk_rows.append(coordinate)
            db.session.bulk_save_objects(bulk_rows)
            inserted_coordinates.extend(bulk_rows)
        db.session.commit()
        return inserted_coordinates
