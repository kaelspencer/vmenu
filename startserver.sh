#!/bin/bash

PROJDIR=$PWD

. ../virtualenv/vmenu/bin/activate

export VMENU_SETTINGS=debug.cfg
#exec celery --app=vmenu.celery worker --logfile /var/log/celery.log &
exec uwsgi -s 127.0.0.1:49152 -w vmenu:app --logto /var/log/uwsgi/vmenu.log
