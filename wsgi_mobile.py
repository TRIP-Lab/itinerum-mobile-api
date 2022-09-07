#!/usr/bin/env python
# Kyle Fitzsimmons, 2016-2018
# WSGI entry script for allowing API to be managed by gunicorn

from mobile.server import create_app

app = create_app()


# http://flask.pocoo.org/snippets/35/
# This may be disabled if API is not hosted behind a reverse proxy
class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app.wsgi_app = ReverseProxied(app.wsgi_app)


if __name__ == "__main__":
    if app.config.get('CONF') == 'development':
        app.run(host=app.config['APP_HOST'],
                port=app.config['APP_PORT'],
                debug=True)
    elif app.config.get('CONF') == 'testing':
        app.run(host=app.config['APP_HOST'],
                port=app.config['APP_PORT'])        
    else:
        app.run(host='0.0.0.0',
                port=app.config['APP_PORT'])
