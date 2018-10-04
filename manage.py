#!/usr/bin/env python
# Kyle Fitzsimmons, 2017-2018
#
# Entry point to run API, migrations and helper scripts
from flask_script import Manager, Server
import logging
import pytest
import sys

from mobile.server import create_app


logging.getLogger('itinerum.mobile').setLevel(logging.WARNING)

app = create_app()
server = Server(port=app.config['APP_PORT'])
manager = Manager(app)
manager.add_command('runserver', server)


@manager.command
def test():
    pytest_args = ['-x', '--cov=mobile', 'tests']
    result = pytest.main(pytest_args)
    sys.exit(result)


if __name__ == '__main__':
    manager.run()
