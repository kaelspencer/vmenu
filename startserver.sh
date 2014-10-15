#!/bin/bash

source /home/kael/code/virtualenv/vmenu/bin/activate

export VMENU_SETTINGS=debug.cfg
exec uwsgi -s 127.0.0.1:49152 -w vmenu:app --logto /var/log/uwsgi/vmenu.log
