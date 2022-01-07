DEFAULT_GOAL := help
.PHONY = help

package = oregoninvasiveshotline
distribution = psu.oit.arc.$(package)
egg_name = $(distribution)
egg_info = $(egg_name).egg-info

venv ?= venv
venv_python ?= python3
venv_autoinstall ?= pip wheel
bin = $(venv)/bin


help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


update_pip_requirements:  ## Updates python dependencies
	@if [ ! -d "./release-env" ]; then python3 -m venv ./release-env; fi
	@./release-env/bin/pip install --upgrade $(venv_autoinstall)
	@./release-env/bin/pip install --upgrade --upgrade-strategy=eager -r requirements.txt
	@./release-env/bin/pip freeze > requirements-frozen.txt
	@sed -i '1 i\--find-links https://packages.wdt.pdx.edu/dist/' requirements-frozen.txt
	@cp ./requirements-frozen.txt ./docker/requirements-frozen.txt
	@sed -i '/psu.oit.arc.oregoninvasiveshotline/d' ./docker/requirements-frozen.txt
	@./release-env/bin/pip list --outdated

client_dependencies:  ## Builds npm dependencies and copies built ('dist') artifacts into static collection directory.
	@yarn install
	@echo "Installing sentry/browser + sentry/tracing..."
	@cp node_modules/@sentry/tracing/build/bundle.tracing.min.js oregoninvasiveshotline/static/js/sentry.browser.min.js
	@echo "Installing js-cookie..."
	@cp node_modules/js-cookie/dist/js.cookie.min.js oregoninvasiveshotline/static/js/
	@echo "Installing jquery..."
	@cp node_modules/jquery/dist/*.min.* oregoninvasiveshotline/static/js/
	@echo "Installing jquery-migrate..."
	@cp node_modules/jquery-migrate/dist/*.min.* oregoninvasiveshotline/static/js/
	@echo "Installing bootstrap..."
	@cp node_modules/bootstrap/dist/js/*.min.js* oregoninvasiveshotline/static/js/
	@cp node_modules/bootstrap/dist/css/*.min.css* oregoninvasiveshotline/static/css/
	@cp node_modules/bootstrap/dist/fonts/* oregoninvasiveshotline/static/fonts/
	@echo "Installing select2..."
	@cp node_modules/select2/dist/js/select2.min.js oregoninvasiveshotline/static/js/
	@cp node_modules/select2/dist/css/select2.min.css oregoninvasiveshotline/static/css/
	@cp node_modules/select2-bootstrap-theme/dist/select2-bootstrap.css oregoninvasiveshotline/static/css/
	@echo "Installing galleria..."
	@cp node_modules/galleria/dist/galleria.min.js* oregoninvasiveshotline/static/js/
	@cp node_modules/galleria/dist/themes/classic/galleria.classic.css oregoninvasiveshotline/static/css/
	@cp node_modules/galleria/dist/themes/classic/galleria.classic.min.js oregoninvasiveshotline/static/js/
	@sed -i "s|galleria.classic.css|../css/galleria.classic.css|" oregoninvasiveshotline/static/js/galleria.classic.min.js
