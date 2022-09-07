#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict


db = SQLAlchemy()


# Web interface tables =========================================================
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                            onupdate=db.func.current_timestamp())


class NewSurveyToken(Base):
    __tablename__ = 'tokens_new_survey'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(14), index=True, unique=True)
    usages = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<NewSurveyToken %s>' % self.token


class WebUserResetPasswordToken(Base):
    __tablename__ = 'tokens_password_reset'
    web_user_id = db.Column(db.Integer, db.ForeignKey('web_users.id'))
    token = db.Column(db.String(60), index=True)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<WebUserResetPasswordToken %d>' % self.id


class ResearcherInviteToken(Base):
    __tablename__ = 'tokens_researcher_invite'
    survey_id = db.Column(db.Integer,
                          db.ForeignKey('surveys.id', ondelete='CASCADE'))
    token = db.Column(db.String(8), index=True)
    usages = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=False)

    __table_args__ = (
        # postgresql does not support partial unique constraints so use
        # a partial unique index instead; this allows us to ensure only
        # True-value 'active' columns are considered within the constraint
        db.Index('researcher_invite_survey_active_idx', survey_id, active,
                 unique=True, postgresql_where=(active)),
    )

    def __repr__(self):
        return '<ResearcherInviteToken %d - %s>' % (self.id, self.token)


class WebUser(Base, UserMixin):
    __tablename__ = 'web_users'
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)
    participant_uuid = db.Column(db.String(36), unique=True)
    survey_id = db.Column(db.Integer,
                          db.ForeignKey('surveys.id', ondelete='CASCADE'),
                          nullable=False)

    roles = db.relationship('WebUserRole',
                            secondary='web_user_role_lookup',
                            backref=db.backref('web_users', lazy='dynamic'))

    reset_password_token = db.relationship('WebUserResetPasswordToken',
                                           backref='web_user',
                                           cascade='all, delete-orphan',
                                           lazy='dynamic')

    def __repr__(self):
        return '<WebUser %s>' % self.email


class WebUserRole(db.Model, RoleMixin):
    __tablename__ = 'web_user_roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    def __repr__(self):
        return '<WebUserRole %r>' % self.name


# Survey tables ================================================================
class Survey(Base):
    __tablename__ = 'surveys'

    name = db.Column(db.String(255), nullable=False, unique=True)
    pretty_name = db.Column(db.String(255))
    language = db.Column(db.String(2))
    about_text = db.Column(db.Text)
    terms_of_service = db.Column(db.Text)
    contact_email = db.Column(db.String(255))
    avatar_uri = db.Column(db.String(255))
    max_survey_days = db.Column(db.Integer, default=14)
    max_prompts = db.Column(db.Integer, default=20)
    gps_accuracy_threshold = db.Column(db.Integer, nullable=False, default=50)
    trip_break_interval = db.Column(db.Integer, nullable=False, default=360)
    trip_break_cold_start_distance = db.Column(db.Integer, nullable=False, default=750)
    trip_subway_buffer = db.Column(db.Integer, nullable=False, default=300)
    last_export = db.Column(MutableDict.as_mutable(JSONB))
    record_acceleration = db.Column(db.Boolean, default=True)
    record_mode = db.Column(db.Boolean, default=True)

    web_users = db.relationship('WebUser',
                                backref='survey',
                                cascade='all, delete-orphan',
                                lazy='dynamic')

    survey_questions = db.relationship('SurveyQuestion',
                                       backref='survey',
                                       cascade='all, delete-orphan',
                                       lazy='dynamic')

    prompt_questions = db.relationship('PromptQuestion',
                                       backref='survey',
                                       cascade='all, delete-orphan',
                                       lazy='dynamic')

    mobile_users = db.relationship('MobileUser',
                                   backref='survey',
                                   cascade='all, delete-orphan',
                                   lazy='dynamic')

    survey_responses = db.relationship('SurveyResponse',
                                       backref='survey',
                                       cascade='all, delete-orphan',
                                       lazy='dynamic')

    prompt_responses = db.relationship('PromptResponse',
                                       backref='survey',
                                       cascade='all, delete-orphan',
                                       lazy='dynamic')

    cancelled_prompts = db.relationship('CancelledPromptResponse',
                                        backref='survey',
                                        cascade='all, delete-orphan',
                                        lazy='dynamic')

    mobile_coordinates = db.relationship('MobileCoordinate',
                                         backref='survey',
                                         cascade='all, delete-orphan',
                                         lazy='dynamic')

    subway_stops = db.relationship('SubwayStop',
                                   backref='survey',
                                   cascade='all, delete-orphan',
                                   lazy='dynamic')

    researcher_invite_token = db.relationship('ResearcherInviteToken',
                                              backref='survey',
                                              cascade='all, delete-orphan',
                                              lazy='dynamic')

    def __repr__(self):
        return '<Survey %d>' % self.id


class SurveyQuestion(db.Model):
    __tablename__ = 'survey_questions'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    question_num = db.Column(db.Integer, index=True)
    question_type = db.Column(db.Integer)
    question_label = db.Column(db.String(100))
    question_text = db.Column(db.String(500))
    answer_required = db.Column(db.Boolean, default=True)

    choices = db.relationship('SurveyQuestionChoice',
                              backref=db.backref('survey_questions'),
                              cascade='all, delete-orphan',
                              order_by='SurveyQuestionChoice.choice_num',
                              lazy='joined')

    def __repr__(self):
        return '<SurveyQuestion survey_id=%s question_num=%s>' % (self.survey_id,
                                                                  self.question_num)


class SurveyQuestionChoice(db.Model):
    __tablename__ = 'survey_question_choices'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey(SurveyQuestion.id, ondelete='CASCADE'))
    choice_num = db.Column(db.Integer)
    choice_text = db.Column(db.String(500))
    choice_field = db.Column(db.String(16))

    def __repr__(self):
        return '<SurveyQuestionChoice %d>' % self.id


class PromptQuestion(db.Model):
    __tablename__ = 'prompt_questions'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    prompt_num = db.Column(db.Integer, index=True)
    prompt_type = db.Column(db.Integer)
    prompt_label = db.Column(db.String(100))
    prompt_text = db.Column(db.String(500))
    answer_required = db.Column(db.Boolean, default=True)

    choices = db.relationship('PromptQuestionChoice',
                              backref=db.backref('prompt_questions'),
                              cascade='all, delete-orphan',
                              order_by='PromptQuestionChoice.choice_num',
                              lazy='joined')

    def __repr__(self):
        return '<PromptQuestion survey_id=%d prompt_num=%s>' % (self.survey_id,
                                                                self.prompt_num)


class PromptQuestionChoice(db.Model):
    __tablename__ = 'prompt_question_choices'

    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey(PromptQuestion.id, ondelete='CASCADE'))
    choice_num = db.Column(db.Integer)
    choice_text = db.Column(db.String(500))
    choice_field = db.Column(db.String(16))

    def __repr__(self):
        return '<PromptQuestionChoice %d>' % self.id


class SubwayStop(db.Model):
    __tablename__ = 'survey_subway_stops'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    latitude = db.Column(db.Numeric(precision=16, scale=10))
    longitude = db.Column(db.Numeric(precision=16, scale=10))

    def __repr__(self):
        return '<SubwayStop %d>' % self.id


# Mobile app response tables ===================================================
class MobileUser(Base):
    __tablename__ = 'mobile_users'

    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    uuid = db.Column(db.String(36), unique=True)
    model = db.Column(db.String(160))
    itinerum_version = db.Column(db.String(16))
    os = db.Column(db.String(16))
    os_version = db.Column(db.String(16))

    survey_response = db.relationship('SurveyResponse',
                                      cascade='all, delete-orphan',
                                      backref='mobile_user',
                                      lazy='dynamic')

    mobile_coordinates = db.relationship('MobileCoordinate',
                                         cascade='all, delete-orphan',
                                         backref='mobile_user',
                                         lazy='dynamic')

    prompt_responses = db.relationship('PromptResponse',
                                       cascade='all, delete-orphan',
                                       backref='mobile_user',
                                       lazy='dynamic')

    cancelled_prompts = db.relationship('CancelledPromptResponse',
                                        cascade='all, delete-orphan',
                                        backref='mobile_user',
                                        lazy='dynamic')

    def __repr__(self):
        return '<MobileUser %d - %s>' % (self.id, self.uuid)


class MobileCoordinate(db.Model):
    __tablename__ = 'mobile_coordinates'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    mobile_id = db.Column(db.Integer, db.ForeignKey(MobileUser.id, ondelete='CASCADE'))
    latitude = db.Column(db.Numeric(precision=10, scale=7))
    longitude = db.Column(db.Numeric(precision=10, scale=7))
    altitude = db.Column(db.Numeric(precision=10, scale=6))
    speed = db.Column(db.Numeric(precision=10, scale=6))
    direction = db.Column(db.Numeric(precision=10, scale=6))
    h_accuracy = db.Column(db.Float)
    v_accuracy = db.Column(db.Float)
    acceleration_x = db.Column(db.Numeric(precision=10, scale=6))
    acceleration_y = db.Column(db.Numeric(precision=10, scale=6))
    acceleration_z = db.Column(db.Numeric(precision=10, scale=6))
    mode_detected = db.Column(db.Integer)
    point_type = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        db.Index('mobile_coordinates_timestamp_idx', timestamp),
        db.Index('mobile_coordinates_survey_timestamp_idx', survey_id, timestamp),
        db.Index('mobile_coordinates_user_timestamp_idx', mobile_id, timestamp)
    )

    def __repr__(self):
        if self.id:
            id = self.id
        else:
            id = ''
        return '<MobileCoordinate %s>' % id


class SurveyResponse(db.Model):
    __tablename__ = 'mobile_survey_responses'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    mobile_id = db.Column(db.Integer, db.ForeignKey(MobileUser.id, ondelete='CASCADE'), unique=True)
    response = db.Column(JSONB)

    __table_args__ = (
        db.Index('survey_response_json_idx',
                 response['gender'],
                 response['age'],
                 response['email']),
    )

    def __repr__(self):
        return '<SurveyResponse %d>' % self.id


class PromptResponse(db.Model):
    __tablename__ = 'mobile_prompt_responses'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    mobile_id = db.Column(db.Integer, db.ForeignKey(MobileUser.id, ondelete='CASCADE'))
    prompt_uuid = db.Column(db.String(36), index=True, nullable=False)
    prompt_num = db.Column(db.Integer, nullable=False)
    response = db.Column(JSONB)
    displayed_at = db.Column(db.DateTime(timezone=True))
    recorded_at = db.Column(db.DateTime(timezone=True),
                            default=db.func.current_timestamp())
    edited_at = db.Column(db.DateTime(timezone=True),
                          default=db.func.current_timestamp())
    latitude = db.Column(db.Numeric(precision=16, scale=10))
    longitude = db.Column(db.Numeric(precision=16, scale=10))

    def __repr__(self):
        return '<PromptResponse id=%d survey_id=%s uuid=%s>' % (self.id,
                                                                self.survey_id,
                                                                self.mobile_id)


class CancelledPromptResponse(db.Model):
    __tablename__ = 'mobile_cancelled_prompt_responses'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    mobile_id = db.Column(db.Integer, db.ForeignKey(MobileUser.id, ondelete='CASCADE'))
    prompt_uuid = db.Column(db.String(36), index=True, unique=True, nullable=False)
    latitude = db.Column(db.Numeric(precision=10, scale=7))
    longitude = db.Column(db.Numeric(precision=10, scale=7))
    displayed_at = db.Column(db.DateTime(timezone=True))
    cancelled_at = db.Column(db.DateTime(timezone=True))
    is_travelling = db.Column(db.Boolean)

    def __repr__(self):
        if self.id:
            id = self.id
        else:
            id = ''        
        return '<MobileCancelledPrompt %s>' % id


# Relationship role tables =====================================================
user_datastore = SQLAlchemyUserDatastore(db, WebUser, WebUserRole)
web_user_role_lookup = db.Table('web_user_role_lookup',
                                db.Column('user_id', db.Integer(), db.ForeignKey('web_users.id', ondelete='CASCADE')),
                                db.Column('role_id', db.Integer(), db.ForeignKey('web_user_roles.id')))


# Statistics tables ============================================================
class Stats(db.Model):
    __tablename__ = 'statistics'

    id = db.Column(db.Integer, primary_key=True)
    last_stats_update = db.Column(db.DateTime(timezone=True))
    last_survey_stats_update = db.Column(db.DateTime(timezone=True))
    last_mobile_stats_update = db.Column(db.DateTime(timezone=True))
    total_surveys = db.Column(db.Integer)

    def __repr__(self):
        return '<Statistics %d>' % self.id


class SurveyStats(db.Model):
    __tablename__ = 'statistics_surveys'

    id = db.Column(db.Integer, primary_key=True)
    total_coordinates = db.Column(db.Integer)
    total_prompts = db.Column(db.Integer)
    total_cancelled_prompts = db.Column(db.Integer)    

    def __repr__(self):
        return '<SurveyStatistics %d>' % self.mobile_id


class MobileUserStats(db.Model):
    __tablename__ = 'statistics_mobile_users'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey(Survey.id, ondelete='CASCADE'))
    mobile_id = db.Column(db.Integer, db.ForeignKey(MobileUser.id, ondelete='CASCADE'), unique=True)
    latest_coordinate = db.Column(db.Integer,
                                  db.ForeignKey(MobileCoordinate.id, ondelete='SET NULL'))
    latest_prompt = db.Column(db.Integer,
                              db.ForeignKey(PromptResponse.id, ondelete='SET NULL'))
    latest_cancelled_prompt = db.Column(db.Integer,
                                        db.ForeignKey(CancelledPromptResponse.id, ondelete='SET NULL'))
    total_coordinates = db.Column(db.Integer)
    total_prompts = db.Column(db.Integer)
    total_cancelled_prompts = db.Column(db.Integer)

    def __repr__(self):
        return '<MobileUserStats %d>' % self.mobile_id
