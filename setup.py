from setuptools import setup, find_packages


VERSION = '1.13.6'


setup(
    name='psu.oit.arc.oregoninvasiveshotline',
    version=VERSION,
    description='Oregon Invasives Hotline',
    author='PSU - OIT - ARC',
    author_email='webteam@pdx.edu',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'psu.oit.wdt.emcee>=1.0.0,<1.1',
        'django~=1.11.25',
        'django-arcutils~=2.24.0',
        'django-bootstrap-form==3.4',
        'django-haystack~=2.8.1',
        'django-perms~=2.0.0',
        'django-pgcli~=0.0.3',
        'celery~=4.3.0',

        'djangorestframework~=3.10.3',
        'elasticsearch>=2.4.0,<3.0.0',
        'Markdown~=3.1.1',
        'Pillow~=6.2.0',
        'psycopg2~=2.8.4',
        'pytz~=2019.3',

        'PyYAML~=5.1.2',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
