import os, locale
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/fyyurapp'

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
BABEL_DEFAULT_LOCALE = 'en'
BABEL_DEFAULT_TIMEZONE = 'UTC'