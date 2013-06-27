#Edit this file.

import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = ''

SQLALCHEMY_DATABASE_URI = ''
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

DWOLLA_API_SECRET = ""
DWOLLA_API_KEY = ""
DWOLLA_API_TOKEN = ""
TWILIO_AUTH_TOKEN = ""

