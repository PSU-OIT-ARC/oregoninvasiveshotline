#!/usr/bin/env python
"""
This script takes the data from the old schema and converts it into the new
schema

It assumes your DATABASES setting has this in it
    'old': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'invhotline',
        'USER': 'username',
        'PASSWORD': 'password',
        'HOST': 'pgsql.rc.pdx.edu',
        'PORT': '',
    },
"""
import urllib.parse
import os
from collections import defaultdict
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotline.settings")

import django
django.setup()

from arcutils.db import dictfetchall
from django.conf import settings
from django.db import connections
from elasticmodels import suspended_updates

from hotline.comments.models import Comment
from hotline.counties.models import County
from hotline.images.models import Image
from hotline.notifications.models import UserNotificationQuery
from hotline.reports.models import Report
from hotline.species.models import Species
from hotline.users.models import User


old = connections['old'].cursor()

# the severity ID and category IDs are assumed to be the same, so we aren't
# importing those

# import the species
old.execute("SELECT id, category_id, severity_id, name_sci, name_comm, remedy, resources FROM issues")
for row in dictfetchall(old):
    species = Species.objects.filter(pk=row['id']).first()
    if not species:
        species = Species(pk=row['id'])

    species.name = row['name_comm'] or ""
    species.scientific_name = row['name_sci'] or ""
    species.remedy = row['remedy'] or ""
    species.resources = row['resources'] or ""
    species.severity_id = row['severity_id']
    species.category_id = row['category_id']
    species.save()

with suspended_updates():
    # create users
    user_id_to_user_id = {}
    report_submitter_user_id = {}
    key_to_user_id = {}
    old.execute("""
    SELECT cardable_id, users.id AS user_id, affiliations, enabled, vcards.id, n_family, n_given, n_prefix, n_suffix, cardable_type, email
    FROM vcards LEFT JOIN users ON vcards.cardable_id = users.id AND cardable_type = 'User'
    ORDER BY cardable_type
    """)
    for row in dictfetchall(old):
        user = User.objects.filter(email=row['email']).first()
        if not user:
            user = User(email=row['email'], is_active=False)

        user.email = row['email']
        user.first_name = row['n_given'] or ""
        user.last_name = row['n_family'] or ""
        user.prefix = row['n_prefix'] or ""
        user.suffix = row['n_suffix'] or ""
        user.is_active = user.is_active or bool(row['enabled'])
        user.affiliations = user.affiliations or (row['affiliations'] or "")
        user.save()

        user_id_to_user_id[row['user_id']] = user.pk
        if row['cardable_type'] == "Submitter":
            report_submitter_user_id[row['cardable_id']] = user.pk

        key_to_user_id[(row['cardable_type'], row['cardable_id'])] = user.pk

    # create reports
    old.execute("""
    SELECT reports.id, category_id, issue_id, reported_category, reported_issue,
    has_sample, issue_desc, private_note, location_desc, reports.created_at, reports.updated_at,
    closed, user_id, edrr_status, lat, lng

    FROM reports LEFT JOIN locations ON locations.locateable_id = reports.id AND locateable_type = 'Report'
    """)
    for row in dictfetchall(old):
        print(row['id'])
        report = Report.objects.filter(report_id=row['id']).first()
        if not report:
            report = Report(pk=row['id'])

        report.reported_category_id = row['reported_category']
        report.reported_species_id = row['reported_issue']
        report.description = row['issue_desc'] or ""
        report.location = row['location_desc'] or ""
        report.has_specimen = row['has_sample']
        report.point = "POINT(" + str(row['lng']) + " " + str(row['lat']) + ")"
        report.created_by_id = report_submitter_user_id[row['id']]
        report.created_on = row['created_at']
        report.claimed_by_id = user_id_to_user_id[row['user_id']]
        report.edrr_status = row['edrr_status'] or 0
        report.actual_species_id = row['issue_id']
        report.county = County.objects.filter(the_geom__intersects=report.point).first()
        report.is_archived = row['closed'] and not row['issue_id']
        report.is_public = row['closed'] and row['issue_id']
        try:
            report.save()
        except Exception as e:
            print(str(e))
            continue

        # create a private comment for the private_note field
        # the PK should be large to avoid colliding with the comments that are imported later
        if row['private_note']:
            Comment(
                pk=100000+report.pk,
                report_id=report.pk,
                body=row['private_note'],
                created_on=row['created_at'],
                visibility=Comment.PRIVATE,
                created_by=User.objects.filter(is_staff=True).first()
            ).save()

    # add comments
    old.execute("""
    SELECT private, id, report_id, annotator_id, annotator_type, body, created_at FROM annotations
    """)
    for row in dictfetchall(old):
        comment = Comment.objects.filter(pk=row['id']).first()
        if not comment:
            comment = Comment(pk=row['id'])

        comment.body = row['body'] or ""
        comment.created_on = row['created_at']
        comment.visibility = Comment.PUBLIC
        try:
            comment.report = Report.objects.get(pk=row['report_id'])
        except Report.DoesNotExist:
            print(row['id'])
            continue

        if row['private']:
            comment.visibility = Comment.PRIVATE

        if row['annotator_type'] == "User":
            comment.created_by_id = user_id_to_user_id[row['annotator_id']]
        elif row['annotator_type'] == "Submitter":
            comment.created_by_id = comment.report.created_by_id
        elif row['annotator_type'] == "Expert":
            comment.created_by_id = key_to_user_id[(row['annotator_type'], row['annotator_id'])]
        else:
            comment.created_by_id = comment.report.created_by_id

        comment.save()

    # add images
    old.execute("""
    SELECT id, imageable_id, imageable_type, filename, created_at, label FROM images
    WHERE imageable_type = 'Report'
    """)
    for row in dictfetchall(old):
        try:
            report = Report.objects.get(pk=row['imageable_id'])
        except Report.DoesNotExist:
            continue

        Image(
            image_id=row['id'],
            image=os.path.relpath(os.path.join(settings.MEDIA_ROOT, "images", ("%04d-" % row['id']) + row['filename']), settings.MEDIA_ROOT),
            name=row['label'],
            created_by_id=report.created_by_id,
            created_on=row['created_at'],
            visibility=Image.PUBLIC,
            report=report,
        ).save()

    # add a notification query for every user
    UserNotificationQuery.objects.filter(name="Imported").delete()
    user_to_query = defaultdict(lambda: defaultdict(list))
    old.execute("SELECT category_id, user_id FROM categories_users INNER JOIN categories ON categories.id = category_id")
    for row in dictfetchall(old):
        user_to_query[row['user_id']]['categories'].append("category_id:%s" % row['category_id'])

    old.execute("SELECT user_id, label FROM regions_users INNER JOIN regions ON regions.id = region_id")
    for row in dictfetchall(old):
        if row['label'].lower() == 'hoodriver':
            row['label'] = "Hood River"
        user_to_query[row['user_id']]['counties'].append('county:(%s)' % row['label'])

    for user_id, info in user_to_query.items():
        categories_query = (" OR ".join(info['categories']))
        counties_query = (" OR ".join(info['counties']))
        if categories_query and counties_query:
            query = ("(%s) AND (%s)" % (categories_query, counties_query))
        elif categories_query:
            query = ("%s" % (categories_query))
        elif counties_query:
            query = ("%s" % (counties_query))

        UserNotificationQuery(name="Imported", user_id=user_id_to_user_id[user_id], query=urllib.parse.urlencode({"querystring": query})).save()
