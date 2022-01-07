import os.path

from emcee.runner.config import YAMLCommandConfiguration
from emcee.runner import command, configs, config
from emcee.runner.commands import remote
from emcee.runner.utils import confirm
from emcee.app.config import YAMLAppConfiguration
from emcee.app import app_configs
from emcee import printer

from emcee.commands.transport import warmup, shell
from emcee.commands.files import copy_file
from emcee.commands.deploy import deploy, list_builds
from emcee.commands.python import virtualenv, install
from emcee.commands.django import manage

from emcee.provision.base import provision_host, patch_host
from emcee.provision.docker import provision_docker
from emcee.provision.python import provision_python, provision_uwsgi
from emcee.provision.gis import provision_gis
from emcee.provision.services import (provision_nginx,
                                      provision_supervisor)
from emcee.provision.secrets import provision_secret, show_secret

from emcee.deploy import deployer, django, docker
from emcee.deploy.services import (push_crontab,
                                   push_supervisor_config,
                                   restart_supervisor)

from emcee.backends.aws.infrastructure.commands import *
from emcee.backends.aws.provision.db import (provision_database,
                                             archive_database,
                                             restore_database,
                                             update_database_ca,
                                             update_database_client)
from emcee.backends.aws.provision.volumes import (provision_volume,
                                                  provision_swapfile)
from emcee.backends.aws.deploy import EC2RemoteProcessor

configs.load(YAMLCommandConfiguration)


@command
def provision(createdb=False):
    # Configure host properties and prepare host platforms
    provision_host()
    provision_python()
    provision_gis()
    provision_uwsgi()

    # Provision application services
    provision_nginx()
    provision_supervisor()
    provision_docker()

    # Provision containers
    printer.header("Initializing container volumes...")
    for service in ['elasticsearch/master',
                    'elasticsearch/node-1',
                    'elasticsearch/node-2',
                    'rabbitmq']:
        services_path = os.path.join(config.remote.path.root, 'services', service)
        remote(('mkdir', '-p', services_path), run_as=config.iam.user)

    # Initialize/prepare attached EBS volume
    provision_volume(mount_point='/vol/store', filesystem='ext4')

    # Initialize swapfile on EBS volume
    provision_swapfile(1024, path='/vol/store')

    # Provision database dependencies
    update_database_client('postgresql', with_devel=True)
    update_database_ca('postgresql')
    if createdb:
        provision_database(backend_options={'with_postgis': True})

    # Provision application secrets
    api_key = input('Enter the Google API key for this project/environment: ')
    provision_secret('GOOGLE_API_KEY', api_key)


@command
def provision_media_assets():
    # Loading data model will cause instantiation of 'ClearableImageInput' which
    # will require that the path '{remote.path.root}/media' exist and be readable
    # by {service.user} so it's execution must be delayed until media assets have
    # been imported.

    # Create media directory on EBS mount and link to app's media root
    printer.header("Creating media directory on EBS volume...")
    remote(('mkdir', '-p', '/vol/store/media'), sudo=True)
    remote(('test', '-h', config.remote.path.media, '||',
            'ln', '-sf', '/vol/store/media', config.remote.path.media), sudo=True)

    # Set the correct permissions on generated assets
    printer.header("Setting permissions on media assets...")
    owner = '{}:{}'.format(config.iam.user, config.services.nginx.group)
    remote(('chown', '-R', owner, '/vol/store/media'), sudo=True)
    remote(('chown', '-R', owner, config.remote.path.media), sudo=True)

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


@command
def provision_data_fixtures():
    # Install static/managed record data
    for fixture in ['counties.json', 'category.json', 'severity.json', 'pages.json']:
        printer.info("Installing fixture '{}'...".format(fixture))
        manage(('loaddata', fixture))

    # Generate icons
    manage(('generate_icons', '--no-input'))


@deployer('services')
class InvasivesServicesDeployer(docker.Deployer):
    remote_processor_cls = EC2RemoteProcessor


class InvasivesRemoteProcessor(EC2RemoteProcessor):
    def activate_application(self, archive_path):
        super().activate_application(archive_path)

        # Reload the supervisor process
        restart_supervisor()


@deployer()
class InvasivesDeployer(django.Deployer):
    remote_processor_cls = InvasivesRemoteProcessor
    app_config_cls = YAMLAppConfiguration

    def setup_application_hosting(self):
        super().setup_application_hosting()

        # Install crontab
        push_crontab(template='assets/crontab')

        # Install supervisor worker configuration
        push_supervisor_config(template='assets/supervisor.conf')
