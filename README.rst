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

In addition to running the Django development server (python manage.py runserver) run npm run --watch from the same
directory to ensure that changes to the front-end code are reflected immediately.
