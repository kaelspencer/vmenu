#!/bin/bash

PROJDIR=$PWD
PIDFILE="$PROJDIR/vmenu.pid"

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

export VMENU_SETTINGS=debug.cfg
exec uwsgi -s 127.0.0.1:49152 -w vmenu:app --daemonize /var/log/uwsgi/vmenu.log --pidfile $PIDFILE
