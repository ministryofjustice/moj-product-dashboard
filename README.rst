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
-  `Plotly.js <https://plot.ly/javascript/>`__(can be installed using :code:`npm install plotly.js --save`)
-  `fetch polyfill <https://github.com/github/fetch>`__(can be installed using :code:`npm install whatwg-fetch --save`)
-  `webpack <https://webpack.github.io/>`__(can be installed using :code:`npm install webpack -g`)


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
