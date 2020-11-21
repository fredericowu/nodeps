#!/bin/bash
source venv/bin/activate
celery -A nodeps.celery beat -l INFO

