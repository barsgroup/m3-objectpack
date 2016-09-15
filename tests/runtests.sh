#!/bin/sh
set -e
export PYTHONPATH=`dirname $0`/..
export DJANGO_SETTINGS_MODULE='tests.settings'

if [ `which django-admin.py` ] ; then
    export DJANGO_ADMIN=`which django-admin.py`
else
    export DJANGO_ADMIN=`which django-admin`
fi

$COVERAGE $DJANGO_ADMIN test \
  --traceback \
  --settings=$DJANGO_SETTINGS_MODULE \
  testapp
