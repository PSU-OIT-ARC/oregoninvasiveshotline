import os.path

from emcee.runner.config import YAMLCommandConfiguration
from emcee.runner import command, configs, config
from emcee.runner.commands import remote
from emcee.runner.utils import confirm
from emcee.app.config import LegacyAppConfiguration
from emcee.app import app_configs
from emcee import printer

from emcee.commands.deploy import deploy
from emcee.commands.python import virtualenv, install
from emcee.commands.django import manage, manage_remote
from emcee.commands.files import copy_file

from emcee.provision.base import provision_host, patch_host
from emcee.provision.python import provision_python
from emcee.provision.gis import provision_gis
from emcee.provision.services import (provision_nginx,
                                      provision_supervisor,
                                      provision_rabbitmq)
from emcee.provision.secrets import show_secret, provision_secret
from emcee.deploy.base import push_crontab, push_supervisor_config
from emcee.deploy.django import Deployer

# from emcee.backends.dev.provision.db import provision_database as provision_database_local
from emcee.backends.aws.infrastructure.commands import *
from emcee.backends.aws.provision.db import provision_database, import_database
from emcee.backends.aws.provision.volumes import provision_volume
from emcee.backends.aws.deploy import EC2RemoteProcessor

DEFAULT_FIXTURES = ('counties.json',)
DEVELOPMENT_FIXTURES = ('dummy_user.json', 'category.json', 'severity.json', 'pages.json')

configs.load('default', 'commands.yml', YAMLCommandConfiguration)
app_configs.load('default', LegacyAppConfiguration)


@command(timed=True)
def init(overwrite=False):
    virtualenv(config.python.venv, overwrite=overwrite)
    install()
    # provision_database_local(drop=overwrite, with_postgis=True)
    manage(('migrate', '--noinput'))
    manage(('loaddata',) + DEFAULT_FIXTURES)
    manage(('loaddata',) + DEVELOPMENT_FIXTURES)
    manage(('generate_icons', '--no-input', '--clean', '--force'))
    manage(('rebuild_index', '--noinput'))


@command
def provision_app(createdb=False):
    # Configure host properties and prepare host platforms
    provision_host(initialize_host=True)
    provision_python()
    provision_gis()
    provision_nginx()
    provision_supervisor()
    provision_rabbitmq()
    api_key = input('Enter the Google API key for this project/environment: ')
    provision_secret('GOOGLE_API_KEY', api_key)

    # Initialize/prepare attached EBS volume
    provision_volume(mount_point='/vol/store')

    if createdb:
        backend_options={'with_postgis': True,
                         'with_devel': True}
        provision_database(backend_options=backend_options)


# Loading data model will cause instantiation of 'ClearableImageInput' which
# will require that the path '{remote.path.root}/media' exist and be readable
# by {service.user} so it's execution must be delayed until media assets have
# been imported.
@command
def provision_media_assets():
    app_media_root = os.path.join(config.remote.path.root, 'media')
    owner = '{}:{}'.format(config.iam.user, config.remote.nginx.group)

    # Create media directory on EBS mount and link to app's media root
    remote(('mkdir', '-p', '/vol/store/media'), sudo=True)
    remote(('mkdir', '-p', app_media_root), sudo=True)
    remote(('test', '-h', config.remote.path.media, '||',
            'ln', '-sf', '/vol/store/media', config.remote.path.media), sudo=True)

    # Set the correct permissions on generated assets
    remote(('chown', '-R', owner, '/vol/store/media'), sudo=True)
    remote(('chown', '-R', owner, app_media_root), sudo=True)

    # Synchronize icons and assorted media assets:
    archive_path = 'media.tar'
    if os.path.exists(archive_path):
        if not confirm("Synchronize media from '{}'?".format(archive_path)):
            return

        copy_file(archive_path, config.remote.path.media)
        remote(('tar', 'xvf', archive_path, '&&',
                'rm', archive_path),
               cd=config.remote.path.media
        )


class InvasivesDeployer(Deployer):
    remote_processor_cls = EC2RemoteProcessor

    def bootstrap_application(self):
        super(InvasivesDeployer, self).bootstrap_application()

        # Install static/managed record data
        manage_remote(('loaddata',) + DEFAULT_FIXTURES)

        # Generate icons
        manage_remote(('generate_icons', '--no-input'))

        # Rebuild search index
        manage_remote(('rebuild_index', '--noinput'))

        # Install crontab
        push_crontab(template='assets/crontab')

    def make_active(self):
        super(InvasivesDeployer, self).make_active()

        push_supervisor_config(template='assets/supervisor.conf')


@command
def deploy_app(rebuild=True):
    deploy(InvasivesDeployer, rebuild=rebuild)
