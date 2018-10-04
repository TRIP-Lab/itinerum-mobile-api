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
logger = logging.getLogger(config.MobileConfig.APP_NAME)


def load_app_config(testing):
    config_env_var = os.environ.get('CONFIG')
    if config_env_var:
        config_env_var = config_env_var.strip().lower()
    if testing is True:
        logger.info(' * Loading TESTING server configuration...')
        return config.MobileTestingConfig

    # fallback on env variable
    elif config_env_var == 'development':
        logger.info(' * Loading DEVELOPMENT server configuration...')
        return config.MobileDevelopmentConfig
    elif config_env_var == 'testing':
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


    # Register mobile API routes - v1 (deprecated) =============================
    api_v1 = Api(app, prefix=app.config['APP_ROOT_V1'])
    api_v1.add_resource(routes.v1.MobileCreateUserRoute, '/create', endpoint='api.create_v1')
    api_v1.add_resource(routes.v1.MobileUpdateDataRoute, '/update', endpoint='api.update_v1')

    # Register mobile API routes - v2 (current) ================================
    # api_v2 = Api(app, prefix=app.config['APP_ROOT_V2'])
    # api_v2.add_resource(routes.v2.MobileCreateUserRoute, '/create', endpoint='api.create_v2')
    # api_v2.add_resource(routes.v2.MobileUpdateDataRoute, '/update', endpoint='api.update_v2')


    # Register health check route for load balancer ============================
    @app.route('/health')
    def ecs_health_check():
        response = {'status': 0}
        return make_response(jsonify(response))

    return app
