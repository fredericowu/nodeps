#!/bin/bash
source venv/bin/activate
celery -A nodeps.celery worker -l INFO -c 1


