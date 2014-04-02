.. pocket_change documentation master file, created by
   sphinx-quickstart on Tue Jan 21 14:13:34 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

Pocket Change is a Flask-based web front end for the Sneeze test reporting
infrastructure.  It allows users to view results of tests.

Installation and Quickstart
===========================

Install Pocket Change with pip: `pip install pocket-change`.  This will get
you all the dependencies, though you'll probably also want pocket.  For that: 
`pip install sneeze-pocket`.

After installation, you must create a config file.  It should be formatted
like a Flask config file (KEY = VALUE) and contain the following values:

* ``SQLALCHEMY_DATABASE_URI`` - A `SQLAlchemy formatted
  <http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html#database-urls>`_
  connection string for the reporting DB
* ``APP_HOST`` - The URL for the Pocket Change host.  The Pocket Change server
  must be discoverable and reachable at this URL from all test running and GUI
  using clients, as well as from the server itself.
* ``APP_PORT`` - The port on which the Pocket Change application is available.
* ``SECRET_KEY`` - Encryption key used by Flask.

Note that other plugins may expose or require other configuration values.

Once the configuration file is created, create an environment variable called
``POCKET_CHANGE_CONFIG`` and set it to the path to the config file.

Now, you should be able to launch the app in your WSGI container of choice
(or start the dev server by running ``python pocket_change/__init__.py``
from the command line).

Repo
====
https://github.com/NYTimes/pocket_change

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

