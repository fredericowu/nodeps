#!/bin/bash
source venv/bin/activate

export DJANGO_ALLOW_ASYNC_UNSAFE=true
python manage.py shell_plus --notebook



