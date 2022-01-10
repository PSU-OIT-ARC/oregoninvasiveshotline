# Changelog for Oregon Invasives Hotline

# 1.15.1 - 2022-01-

- Uses Django 3.2 LTS

# 1.15.0 - 2022-01-07

- Replaces use of Elasticsearch with PostgreSQL full-text search.

## 1.14.1 - 2021-02-10

- Drops support for Python<3.7.
- Updates client Javascript dependencies and replaces hard-
  coded/bundled packages with specifiers in 'package.json'
  and utility scripts.

## 1.14.0 - 2021-01-22

- Uses cloud-config 20210115 release.
- Uses Emcee 1.0.7.
- Uses Django 2.2 LTS.
- Drops support for Python<3.6.
- Drops dependencies on unmaintained, historical organizational
  packages 'django-arcutils', 'django-perms'.
- Adds modern configuration of Sentry clients.
- Adds tooling for frontend client dependency management.
- Updates, refactors docker container construction.
- Updates project dependencies to support current releases:
  - Pillow 8.0
  - celery 5.0
  - djangorestframework 3.12
  - django-haystack 3.0

## 1.13.7 - 2020-02-12

### Maintenance

- Uses Emcee 1.0.4.
- Replaces use of AWS Elasticsearch service in favor of a locally-
  administered, container-based ES cluster.
- Updates Python dependencies.

## 1.13.6 - 2020-01-21

### Maintenance

- Replaces use of assets hosted on 'cdn.research.pdx.edu'.

## 1.13.5 - 2019-10-22

### Maintenance

- Uses Emcee 1.0.0.
- Updates Python dependencies.

## 1.13.4 - 2019-08-19

### Maintenance

- Uses Emcee 1.0.0.rc9.

## 1.13.3 - 2019-04-22

### Maintenance

- Adds formal support for Python 3.7.
- Uses PostgreSQL 10 / PostGIS 2.4 in docker and travis environments.
- Adds separate local.test.cfg for test env configuration.
- Updates Python dependencies.
- Adds additional requirement to avoid vulnerable releases
  of the PyYAML package.

## 1.13.2 - 2018-10-19

### Added

- Manage Google API keys with emcee and AWS ssm.

### Fixed

- Adds local.docker.cfg for docker env configuration.
- Revise wsgi file to be closer to Django standard.

### Maintenance

- Update Python dependencies.

## 1.13.1 - 2018-06-27

### Fixed

- Uses Emcee 1.0.0.rc7 to avoid on-going STS credential expiry
  issues related to the use of Elasticsearch connections.
- Revises and corrects construction and runtime behavior of
  docker containers to be more robust.

## 1.13.0 - 2018-06-21

### Added

- Configures the project to use Emcee to support AWS deployment.
- Replaces frail code paths responsible for triggering email
  notifications with Celery-based out-of-band tasks.

### Fixed

- Addresses authentication issues related to public login attempts
  and the behavior in Django >= 1.10.
- Uses appropriate Haystack backend for Elasticsearch>2.0,<3.0

### Maintenance

- Adds client-side Raven integration.
- Replaces hard-coded use of email 'From' headers.
- Revises implementation of URI builder to preclude the requirement
  for passing around 'HttpRequest' objects.
- Adds crontab to facilitate scheduled operations.

## 1.12.1 - 2018-03-12

### Fixed

- Fixed Haystack indexing error on report.claimed_by_id

### Maintenance

- Bump Haystack to newest release 2.8

## 1.12.0 - 2018-02-21

### Maintenance

- Update to Django 1.11.x
- Update python dependencies
- Update JS dependencies

### Feature

- Added address Geocoder (Google maps API) to report form

## 1.11.0 - 2017-10-12

### Added

- Add claimed by me search filter tab
- Mangers claim unclaimed report when commenting
- Urlize comment body if manager
- Add Docker config for running services in dev

### Fixed

- Add DISTRIBUTION setting in local.base.cfg
- Corrects static asset reference.

### Miscellaneous

- Pin DRF requirement to < 3.7
- Updates package dependencies.
- Revises docker-compose definitions.
- Remove mommy-spatial-generators dependency
- Various build/deploy tooling updates

## 1.10.0 - 2016-08-16

- Change default visibility of comments to protected (only allow
  reporter and commenter to view).
- Constrain  Django Haystack version.

## 1.9.0 - 2016-05-23

### Added

- Quick nav on all admin pages (nav pills at top of page). This is much
  nicer than making admins return to the Admin home page to get to
  another admin page.
- List, edit, and delete views of search subscriptions for admins.
- First & last page pagination controls.
- Additional help text on report form; in particular, which parts of the
  form will be public & private.
- Google Analytics.

### Changed

- Switched to standard Bootstrap pagination controls instead of custom
  markup.

### Fixed

- Moved admin panel out of `species` app.
- Corrected a regression in `Invite.create()` introduced in a6d2022 due
  to incorrect use of `Invite.objects.get_or_create()`. Fixed related
  tests too.

### Miscellaneous

- Clean up various bits of project config.
- Upgraded Python dependencies.

## 1.8.1 - 2016-03-14

### Fixed

- Make page edit form render for "hidden" pages.
