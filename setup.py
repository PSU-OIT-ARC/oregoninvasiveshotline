from setuptools import setup, find_packages


VERSION = '1.13.0.dev0'


setup(
    name='psu.oit.arc.oregoninvasiveshotline',
    version=VERSION,
    description='Oregon Invasives Hotline',
    author='PSU - OIT - ARC',
    author_email='consultants@pdx.edu',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'psu.oit.wdt.emcee>=1.0.0.rc2',
        'django>=1.11.10,<2.0',
        'django-arcutils>=2.24.0',
        'django-bootstrap-form>=3.3',
        'django-haystack>=2.8',
        'django-perms>=2.0.0',
        'django-pgcli>=0.0.2',

        'djangorestframework>=3.7',
        'elasticsearch>=2.0.0,<3.0.0',
        'Markdown>=2.6.11',
        #'Pillow=4.3.0,
        'Pillow>=5.0',  #can't move to 5 until prod python is > 3.3
        'psycopg2>=2.7.4',
        'pytz>=2018.3',
        #'olefile==0.44' #must specify while using py3.3
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
)
