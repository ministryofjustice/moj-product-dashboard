#
# MoJ Product Dashboard Dockerfile all environments
#
FROM ubuntu:xenial

RUN apt-get update && \
    apt-get install -y software-properties-common python-software-properties \
    curl

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash

RUN apt-get update && \
    apt-get install -y \
        build-essential git python3-all python3-all-dev python3-setuptools \
        libpq-dev libpcre3-dev python3-pip python-pip ruby ruby-dev nodejs

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10

WORKDIR /app
RUN mkdir -p /app/static

RUN pip3 install -U setuptools pip wheel virtualenv uwsgi
RUN virtualenv -p python3 venv

# cache python packages, unless requirements change
ADD ./requirements /app/requirements
RUN venv/bin/pip install -r requirements/base.txt

ADD . /app
RUN rm -rf /app/.git

RUN cd /app && npm install --unsafe-perm && npm run build

RUN cd /app && /app/venv/bin/python manage.py collectstatic --noinput

EXPOSE 8000
CMD bash /app/docker/run.sh


