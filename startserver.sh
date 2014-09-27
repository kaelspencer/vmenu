#!/bin/bash

PROJDIR=$PWD
PIDFILE="$PROJDIR/vmenu.pid"

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

. ../virtualenv/vmenu/bin/activate

export VMENU_SETTINGS=debug.cfg
#exec celery --app=vmenu.celery worker --logfile /var/log/celery.log &
exec uwsgi -s 127.0.0.1:49152 -w vmenu:app --daemonize /var/log/uwsgi/vmenu.log --pidfile $PIDFILE
