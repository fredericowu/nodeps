#!/bin/bash
source venv/bin/activate
source .env
celery -A nodeps.celery worker -l INFO -c 1


