#
# MoJ Product Dashboard Dockerfile all environments
#
# FROM python:3.5
FROM ubuntu:xenial
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y software-properties-common python-software-properties \
    curl

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash

RUN apt-get update && \
    apt-get install -y \
        build-essential git python3-all python3-all-dev python3-setuptools \
        libpq-dev libpcre3-dev python3-pip python-pip ruby ruby-dev nodejs \
        python3-gdbm

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10

WORKDIR /app
RUN mkdir -p /app/static

RUN pip3 install -U setuptools pip wheel uwsgi

# cache python packages, unless requirements change
ADD ./requirements /app/requirements
RUN pip3 install -r requirements/base.txt

ADD . /app
RUN rm -rf /app/.git

RUN cd /app && npm install --unsafe-perm && npm run build

RUN cd /app && /usr/bin/python3 manage.py collectstatic --noinput

ENTRYPOINT bash /app/docker/run.sh ${PORT:-8000}
