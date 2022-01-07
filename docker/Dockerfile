FROM python:3.7-buster
MAINTAINER Thom Linton <tlinton@pdx.edu>


# Install project dependencies
RUN apt update -y && apt install -y \
  build-essential \
  binutils libgdal-dev proj-bin

# Set build arguments
ARG APP_PYTHON=python3.7
ARG APP_ENV=/opt/venv

# Set environment variable defaults
ENV PROJECT_NAME oregoninvasiveshotline
ENV PROJECT_DIR /webapps/${PROJECT_NAME}
ENV APP_USER invasives
ENV APP_GROUP invasives

# Export build arguments as environment variables
ENV APP_PYTHON ${APP_PYTHON}
ENV APP_ENV ${APP_ENV}

# Configure user
RUN groupadd "${APP_GROUP}" || echo "Group already exists"
RUN useradd -m -g "${APP_GROUP}" "${APP_USER}" || echo "User already exists"

# Prepare virtual environment package requirements
COPY --chown=${APP_USER}:${APP_GROUP} /requirements-frozen.txt /requirements-frozen.txt

# Prepare virtual environment
RUN mkdir -p ${APP_ENV}
RUN chown ${APP_USER}:${APP_GROUP} ${APP_ENV}

# Configure python virtual environment
USER ${APP_USER}
RUN ${APP_PYTHON} -m venv ${APP_ENV}
RUN ${APP_ENV}/bin/pip install --upgrade pip wheel
RUN ${APP_ENV}/bin/pip install -r /requirements-frozen.txt
RUN ${APP_ENV}/bin/pip cache purge

# Install container entrypoint
WORKDIR ${PROJECT_DIR}
COPY ./entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
