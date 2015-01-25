#!/bin/bash

source /home/kael/code/virtualenv/vmenu/bin/activate
export VMENU_SETTINGS=debug.cfg
exec celery --app=vmenu.celery worker --logfile /var/log/celery.log
