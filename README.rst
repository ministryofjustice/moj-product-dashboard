=====================
MOJ Product Dashboard
=====================

.. image:: https://codeclimate.com/github/ministryofjustice/moj-product-dashboard/badges/gpa.svg
   :target: https://codeclimate.com/github/ministryofjustice/moj-product-dashboard
   :alt: Code Climate

.. image:: https://codeclimate.com/github/ministryofjustice/moj-product-dashboard/badges/coverage.svg
   :target: https://codeclimate.com/github/ministryofjustice/moj-product-dashboard/coverage
   :alt: Test Coverage

.. image:: https://codeclimate.com/github/ministryofjustice/moj-product-dashboard/badges/issue_count.svg
   :target: https://codeclimate.com/github/ministryofjustice/moj-product-dashboard
   :alt: Issue Count

Product dashboard for MoJ products.

.. contents:: :depth: 1

Dependencies
============

-  `Python 3.5 <http://www.python.org/>`__ (can be installed using :code:`brew install python3`)
-  `Virtualenv <http://www.virtualenv.org/en/latest/>`__ (can be installed using :code:`pip3 install virtualenv`)
-  `nodejs.org <http://nodejs.org/>`__ (v6.2.0 - can be installed using `nvm <https://github.com/creationix/nvm>`_)


Installation
============

Clone the repository:

::

    git clone git@github.com:ministryofjustice/moj-product-dashboard.git

Next, create the environment and start it up:

::

    virtualenv env --python=`which python3` --prompt=\(dashboard)\

    source env/bin/activate

Update pip to the latest version:

::

    pip install -U pip

Install python dependencies:

::

    pip install -r requirements/local.txt

Install frontend dependencies:

::

    npm install

Development
============

Run the Django development server:

::

    python manage.py runserver

Watch and compile JS and CSS when code changes detected:

::

    npm run watch


Build compressed JS and CSS:

::

    npm run build


Testing
=======

Run unit tests for python code:

::

    py.test --cov=dashboard --cov-report term-missing


Run unit tests for JS code:

::

    npm run test


Generate coverage report for JS code:

::

    npm run test -- --coverage


Watch and rerun JS unit tests when code changes detected:

::

    npm run test -- --watch


Background Tasks
================

Background tasks on AWS are run using Celery and SQS. Locally you will need to install rabbitmq-server instead of SQS.

::

    brew install rabbitmq

Copy BROCKER_URL in to your local.py

::

    BROKER_URL = "amqp://"
    BROKER_TRANSPORT_OPTIONS = {}

Then run rabbitmq-server it with

::

    rabbitmq-server

and finally run cellery with

::

    celery -A dashboard worker -B -l info


Heroku
======

Start Docker

::
    docker-machine start default

check the repo out and run these commands once you have creates your app

::

    heroku plugins:install heroku-container-tools
    heroku plugins:install heroku-container-registry
    heroku container:login
    heroku addons:create heroku-postgresql:standard-2x --app moj-product-dashboard
    heroku addons:create cloudamqp:lemur --app moj-product-dashboard
    heroku addons:create heroku-redis:hobby-dev --app moj-product-dashboard

Then run

::

    heroku config --app moj-product-dashboard

to get the DATABASE_URL and CLOUDAMQP_URL to set up application env vars

::

    heroku config:set DB_HOST=xx --app moj-product-dashboard
    heroku config:set DB_NAME=xx --app moj-product-dashboard
    heroku config:set DB_PASSWORD=xx --app moj-product-dashboard
    heroku config:set DB_PORT=5432 --app moj-product-dashboard
    heroku config:set DB_USERNAME=xx --app moj-product-dashboard

    heroku config:set CELERY_BROKER_URL=amqp://xx:xxM@buck.rmq.cloudamqp.com/xx --app moj-product-dashboard

    heroku config:set REDIS_URL:redis://xx:xx@xx.compute-1.amazonaws.com:10109  --app moj-product-dashboard

Set other env vars

::

    heroku config:set DEBUG=True --app moj-product-dashboard
    heroku config:set PORT=8000 --app moj-product-dashboard

Then push and start the app

::

    heroku container:push web --app moj-product-dashboard

