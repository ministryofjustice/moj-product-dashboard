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

Check the repo out and run these commands once you have created your app

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

to get the DATABASE_URL, REDIS_URL and CLOUDAMQP_URL to set up application env vars

::

    heroku config:set DB_HOST=xx --app moj-product-dashboard
    heroku config:set DB_NAME=xx --app moj-product-dashboard
    heroku config:set DB_PASSWORD=xx --app moj-product-dashboard
    heroku config:set DB_PORT=5432 --app moj-product-dashboard
    heroku config:set DB_USERNAME=xx --app moj-product-dashboard

    heroku config:set CELERY_BROKER_URL=amqp://xx:xxM@buck.rmq.cloudamqp.com/xx --app moj-product-dashboard

    heroku config:set REDIS_URL:redis://xx:xx@xx.compute-1.amazonaws.com:10109  --app moj-product-dashboard

    heroku config:set FLOAT_API_TOKEN:xx --app moj-product-dashboard
    heroku config:set FLOAT_URL:xx --app moj-product-dashboard

Set other env vars

::

    heroku config:set DEBUG=True --app moj-product-dashboard

Then push and start the app

::

    heroku container:push web --app moj-product-dashboard



Amazon ECS
==========

You can get this running on Amazon ECS but creating a stack with the cloudformation template in ```cloudformation/template.yaml```

1. Create a Hosted Zone in AWS Route53 for the domain you would like
2. Upload the cloudformation template to AWS either via the AWS Console or via the AWS CLI. You will have to confirm the Certificate creation - maybe via email.
3. Create an A Record in the hosted zone and point it to the load balancer created in the stack
4. Create a local.py file in the dashboard/settings directory
5. Create an IAM user and give it permissions to the SQS Queue created in the stack
 - Create an API key and token from the IAM user and and add the following to the local.py file

::

    BROKER_URL = 'sqs://{API_TOKEN}:{API_KEY}@'

6. Add your Float API key to local.py

::

    FLOAT_API_TOKEN = '{YOUR_FLOAT_API_TOKEN}'
    FLOAT_URL = '{URL TO YOUR FLOAT API}'

7. Build a docker image - find your image repository from ECS Management in AWS Console

::

    docker build -t dashboard .
    docker tag dashboard:latest {YOUR IMAGE REPOSITRY}/dashboard:latest
    docker push {YOUR IMAGE REPOSITRY}/dashboard:latest

8. Re-run the task for the Cluster in ECS Management in AWS Console
