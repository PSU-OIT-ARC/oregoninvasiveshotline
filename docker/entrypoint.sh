#!/bin/bash
set -e


cd ${PROJECT_DIR}

# Bootstrap application if requested
if [[ ${APP_BOOTSTRAP} == "yes" ]]; then
    ${APP_ENV}/bin/python manage.py migrate --noinput
    ${APP_ENV}/bin/python manage.py loaddata counties.json
    ${APP_ENV}/bin/python manage.py loaddata dummy_user.json category.json severity.json pages.json
    ${APP_ENV}/bin/python manage.py generate_icons --no-input --clean --force
fi

# Select the entrypoint given the APP_SERVICE
if [[ ${APP_SERVICE} == "wsgi" ]]; then
    exec ${APP_ENV}/bin/python manage.py runserver 0.0.0.0:8000
elif [[ ${APP_SERVICE} == "celery" ]]; then
    exec ${APP_ENV}/bin/celery -A oregoninvasiveshotline worker -l INFO
elif [[ ${APP_SERVICE} == "test" ]]; then
    ${APP_ENV}/bin/pip install -r requirements-dev.txt
    exec ${APP_ENV}/bin/python manage.py test
fi
