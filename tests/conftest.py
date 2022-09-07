#!/usr/bin/env python
# Kyle Fitzsimmons, 2016-2018
#
# Unit tests for mobile API
# Based on: https://github.com/vitalk/flask-apify/blob/master/tests
#           http://alexmic.net/flask-sqlalchemy-pytest/
from flask_security import Security, SQLAlchemyUserDatastore
import os
import pytest

from admin_prepopulate_survey import prepopulate
from config import MobileTestingConfig
from models import user_datastore, WebUser, WebUserRole
from mobile.server import create_app
from mobile.database import db as _db



@pytest.fixture(scope='session')
def app(request):
    app = create_app(testing=True)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


# Session-wide test database
@pytest.fixture(scope='session')
def db(app, request):
    app.config['SECURITY_PASSWORD_SALT'] = 'ChangeMe'
    _db.app = app
    _db.create_all()

    user_datastore = SQLAlchemyUserDatastore(_db, WebUser, WebUserRole)
    Security(app, user_datastore)
    prepopulate(_db, './tests/test-survey-schema.json')
    yield _db

    _db.session.close()
    _db.drop_all()


# Creates a new database session for a test
@pytest.fixture(scope='function')
def session(db, request):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session
