#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Kyle Fitzsimmons, 2017-2018
from flask import Flask, jsonify, make_response
from flask_restful import Api
import logging
import os
from raven.contrib.flask import Sentry

import config
from mobile import routes
from models import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_app_config(testing):
    if testing is True:
        logger.info(' * Loading TESTING server configuration...')
        return config.MobileTestingConfig

    # fallback on env variable
    elif os.environ.get('CONFIG') == 'debug':
        logger.info(' * Loading DEVELOPMENT server configuration...')
        return config.MobileDevelopmentConfig
    elif os.environ.get('CONFIG') == 'testing':
        logger.info(' * Loading TESTING server configuration...')
        return config.MobileTestingConfig
    else:
        logger.info(' * Loading PRODUCTION server configuration...')
        return config.MobileProductionConfig


def create_app(testing=False):
    app = Flask(__name__)
    cfg = load_app_config(testing)
    app.config.from_object(cfg)
    db.init_app(app)    

    # Connect Sentry.io error reporting ========================================
    if app.config['CONF'] == 'production':
        logger.info(' * Starting Sentry.io reporting for application...')
        Sentry(app, dsn='https://{key}:{secret}@sentry.io/{app_id}'.format(
            key=app.config['SENTRY_KEY'],
            secret=app.config['SENTRY_SECRET'],
            app_id=app.config['SENTRY_APP_ID']))
    else:
        logger.info(' * Sentry.io reporting disabled.')


    # Register mobile API routes ===============================================
    api = Api(app, prefix=app.config['APP_ROOT'])
    api.add_resource(routes.MobileCreateUserRoute, '/create')
    api.add_resource(routes.MobileUpdateDataRoute, '/update')

    # Register health check route for load balancer ============================
    @app.route('/health')
    def ecs_health_check():
        response = {'status': 0}
        return make_response(jsonify(response))

    return app
