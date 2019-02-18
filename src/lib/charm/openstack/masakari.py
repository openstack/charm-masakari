import collections
import socket
import subprocess
import tempfile

import charmhelpers.core.hookenv as hookenv
import charms_openstack.charm
import charms_openstack.ip as os_ip
import charmhelpers.contrib.openstack.utils as ch_os_utils


# import charms_openstack.sdn.odl as odl
# import charms_openstack.sdn.ovs as ovs

MASAKARI_WSGI_CONF = '/etc/apache2/sites-enabled/masakari-api.conf'

charms_openstack.charm.use_defaults('charm.default-select-release')

class MasakariCharm(charms_openstack.charm.HAOpenStackCharm):

    # Internal name of charm
    service_name = name = 'masakari'

    # First release supported
    release = 'mitaka'

    # List of packages to install for this charm
    packages = ['libapache2-mod-wsgi', 'apache2', 'python-apt', 'cinder-common']

    api_ports = {
        'masakari': {
            os_ip.PUBLIC: 15868,
            os_ip.ADMIN: 15868,
            os_ip.INTERNAL: 15868,
        }
    }

    service_type = 'masakari'
    default_service = 'masakari'
    services = ['haproxy', 'apache2', 'masakari-engine']

    required_relations = ['shared-db', 'amqp', 'identity-service']

    restart_map = {
        '/etc/masakari/masakari.conf': services,
        MASAKARI_WSGI_CONF: services,
    }

    ha_resources = ['vips', 'haproxy', 'dnsha']

    release_pkg = 'cinder-common'

    package_codenames = {
        'masakari-common': collections.OrderedDict([
            ('2', 'mitaka'),
            ('3', 'newton'),
            ('4', 'ocata'),
        ]),
    }


    sync_cmd = ['masakari-manage', '--config-file', '/etc/masakari/masakari.conf', 'db', 'sync']

    def get_amqp_credentials(self):
        return ('masakari', 'masakari')

    def get_database_setup(self):
        return [{
            'database': 'masakari',
            'username': 'masakari'}]

    @property
    def public_url(self):
        return super().public_url + "/v1/%(tenant_id)s"

    @property
    def admin_url(self):
        return super().admin_url + "/v1/%(tenant_id)s"

    @property
    def internal_url(self):
        return super().internal_url + "/v1/%(tenant_id)s"

    # XXX THIS IS A TEMPORARY WORKAROUND AND SHOULD NOT BE INCLUDED IN
    # ANY DEPLOYMENTS OTHER THAN POCs
    def install(self):
        super(MasakariCharm, self).install()
        os_release = ch_os_utils.get_os_codename_package('cinder-common')
        with tempfile.TemporaryDirectory() as tmpdirname:
            git_dir = '{}/masakari'.format(tmpdirname)
            subprocess.check_call([
                'git', 'clone', '-b', 'stable/{}'.format(os_release),
                'https://github.com/openstack/masakari.git', git_dir])
            subprocess.check_call([
                'sudo', 'python', 'setup.py', 'install'], cwd=git_dir)
        subprocess.check_call(['mkdir', '-p', '/var/lock/masakari', '/var/log/masakari', '/var/lib/masakari'])
        subprocess.check_call(['cp', 'templates/masakari-engine.service', '/lib/systemd/system'])
        subprocess.check_call(['systemctl', 'daemon-reload'])
        subprocess.check_call(['systemctl', 'start', 'masakari-engine'])
