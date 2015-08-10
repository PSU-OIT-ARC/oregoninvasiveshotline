.PHONY: run install clean coverage reload

PROJECT_NAME = hotline
VENV_DIR ?= .env
# centos puts pg_config in weird places. We run postgres 9.1 and 9.3 in prod and dev
# respectively.
PG_DIRS = /usr/pgsql-9.1/bin:/usr/pgsql-9.3/bin

PYTHON = python3
MANAGE = python manage.py
HOST ?= 0.0.0.0
PORT ?= 8000

export PATH:=$(VENV_DIR)/bin:$(PATH):$(PG_DIRS)

run:
	$(MANAGE) runserver $(HOST):$(PORT)

init:
	rm -rf $(VENV_DIR)
	@$(MAKE) $(VENV_DIR)
	dropdb --if-exists $(PROJECT_NAME)
	createdb $(PROJECT_NAME)
	psql -c "CREATE EXTENSION postgis" $(PROJECT_NAME)
	@$(MAKE) reload
	$(MANAGE) loaddata dummy_user.json category.json severity.json species.json counties.json
	psql $(PROJECT_NAME) < pages_backup.sql 

clean:
	find . -iname "*.pyc" -delete
	find . -iname "*.pyo" -delete
	find . -iname "__pycache__" -delete

coverage:
	coverage run ./manage.py test --keepdb && coverage html && cd htmlcov && python -m http.server 9000

test:
	$(MANAGE) test --keepdb && flake8 && isort -rc --diff $(PROJECT_NAME)

reload:
	$(MANAGE) migrate
	$(MANAGE) collectstatic --noinput
	$(MANAGE) rebuild_index --clopen --noinput
	touch $(PROJECT_NAME)/wsgi.py

$(VENV_DIR):
	$(PYTHON) -m venv .env
	curl https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py | python
	pip install -r requirements.txt
