#!/bin/bash
set -e


cd ${PROJECT_DIR}
make install venv=${APP_VENV}
${APP_VENV}/bin/mc -e docker init

if [[ ${APP_SERVICE} == "wsgi" ]]; then
    exec ${APP_VENV}/bin/python manage.py runserver 0.0.0.0:8000
elif [[ ${APP_SERVICE} == "celery" ]]; then
    exec ${APP_VENV}/bin/celery -A oregoninvasiveshotline worker -l INFO
fi
