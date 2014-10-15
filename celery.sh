#!/bin/bash

source /home/kael/code/virtualenv/vmenu/bin/activate

exec celery --app=vmenu.celery worker --logfile /var/log/celery.log
