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

Create the postgres database named dashboard:

::

    createdb dashboard

Create database tables

::

    python manager.py migrate

Load auth group, permissions and test users:

::

    python manager.py loaddata dashboard/apps/dashboard/fixtures/*

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

To use the AWS CLI you will need to create an IAM user in your AWS account and configure a profile. See `CLI - getting started <http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`__ For more info on how to do this. Remember your profile name as you will need it when running the login command below.

You can get this running on Amazon ECS but creating a stack with the cloudformation template in ```cloudformation/template.yaml```

The Template can also be produced/edited with this repository

`https://github.com/s-block/ecs/ <https://github.com/s-block/ecs/>`__ (by running :code:`python create.py`)

1. Create a Key Pair that you want your instances to have so you can ssh in to them - need to enter this when creating the stack
2. Create a Hosted Zone in AWS Route53 for the domain you would like
3. Upload the cloudformation template to AWS either via the AWS Console or via the AWS CLI. You will have to confirm the Certificate creation - maybe via email. Most of the fields are obvious but some that aren't are:
 - Stack name: can be anything, will be used as the repository name
 - DomainName: domain to create the Certificate for
 - KeyName: name of Key Pair created in step one. Will bee needed to ssh in to any instances
 - SecretKey: Used to set the ENV var SECRET_KEY to be used by the Django app
 - WebAppRevision: Docker tag to automatically build when updated. 'master' or 'prod' or anything you like.

4. Create an A Record in the hosted zone and point it to the load balancer created in the stack
5. Create a local.py file in the dashboard/settings directory
6. Build a docker image - find your image repository from ECS Management in AWS Console

::

    aws ecr get-login --profile {YOUR_PROFILE_NAME} --region eu-west-1
    {RUN_COMMAND_RETURNED_FROM_ABOVE}

    docker build -t {STACK_NAME} .
    docker tag {STACK_NAME}:{WebAppRevision} {YOUR_IMAGE_REPOSITRY}/{STACK_NAME}:{WebAppRevision}
    docker push {YOUR_IMAGE_REPOSITRY}/{STACK_NAME}:{WebAppRevision}

7. Re-run the task for the Cluster in ECS Management in AWS Console


Create Finance Admin User
=========================

Only users with the role of ``finance`` can access sensitive data like people's salary or daily rates. Only users with both roles of ``finance`` and ``admin`` can create finance users. Therefore to get the system running, a finance admin user is needed.

This command will create a finance admin user if one doesn't already exist, so it's safe to be used by build system to run in every build without causing additional side effects

::

    python manager.py ensure_finance_amdin_user --username ${username} --password ${password}


To create an extra finance admin user, use the --force option

::

    python manager.py ensure_finance_amdin_user --username ${username} --password ${password} --force
