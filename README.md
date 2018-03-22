# Oregon Invasive Species Hotline

This project allows members of the public to submit reports of invasive species for experts to
review. Experts can login and review the reports, comment on them, and make a final determination
about the species that was reported

## Technology stack

- PostgreSQL 9.6
- PostGIS 2.x
- Elasticsearch 2.x
- Python 3.6
- Django 1.11.x
- Google Maps

## Getting started

To build the application dependencies in your host's environment:

    make init

To use the provided Docker container definitions:

    venv/bin/pip install -r requirements.txt
    venv/bin/docker-compose up -d

To authenticate with the provided default user:

    username: foobar@example.com
    password: foobar

## Deploying

This project using the Emcee tooling to define and orchestrate resource provisioning and deployment.
See the AWS cloudformation templates in `cloudformation` and the command definitions in `commands.py`
for more information.

## Notable Hackiness

The Sites framework is used here only so we can use flatpages. To avoid having to update the stupid
domain column all the time, the Site.objects attribute has been monkey-patched in the `utils`
module so it returns whatever domain is currently being used.

There is a "subscribe to search" feature that allows an active user of the system to perform
a search on the reports list page and then subscribe to it. Meaning: whenever a new report is
submitted that matches that search, the subscriber will get an email notification about it. The way
this is implemented is the `request.GET` parameters are saved to the `UserNotificationQuery` model
as a string like "querystring=foobar&category-4=142". When a report is submitted, a new
`ReportSearchForm` is instantiated and passed the decoded GET parameters that were saved in the
`UserNotificationQuery` model. The `search()` method on the form is called, and if the results
contains that newly submitted report, the user gets an email. This is an expensive process, so it
runs in a separate thread.

Because cron jobs tend to get abandoned around here, the Elasticsearch index is rebuilt early in
the morning via a daily task runner process.
