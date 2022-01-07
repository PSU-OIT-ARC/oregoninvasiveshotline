# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import sys
import re
import os


if sys.version_info < (3, 7):
    raise Exception('Oregon Invasives Hotline requires Python versions 3.7 or later.')

# Metadata extraction by parsing 'oregoninvasiveshotline module directly.
#   https://github.com/celery/kombu/blob/master/setup.py
re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')
re_doc = re.compile(r'^"""(.+?)"""')

def add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, attr_value.strip("\"'")),)

def add_doc(m):
    return (('doc', m.groups()[0]),)

pats = {re_meta: add_default, re_doc: add_doc}
here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, 'oregoninvasiveshotline/__init__.py'))

try:
    meta = {}
    for line in meta_fh:
        if line.strip() == '# -eof meta-':
            break
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))
finally:
    meta_fh.close()

setup(
    name='psu.oit.arc.oregoninvasiveshotline',
    version=meta['version'],
    author=meta['author'],
    description=meta['doc'],
    long_description=open('README.md').read(),
    url=meta['homepage'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'pytz',
        'Markdown~=3.3.0',
        'Pillow~=9.0.0',
        'Django~=2.2.0',
        # Django 2.2 can only tolerate psycopg2<2.9
        # Refs: https://github.com/psycopg/psycopg2/issues/1293
        'psycopg2~=2.8.6',
        'celery~=5.2.0',
        'djangorestframework~=3.13.0',
        'django-bootstrap-form==3.4',
        'psu.oit.wdt.emcee[aws]~=1.1.0b3',
        'sentry-sdk~=1.5.0',
    ],
    extras_require={
        'dev': [
            'bpython',
            'coverage',
            'flake8',
            'model_mommy',
            'docker-compose'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable'
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
