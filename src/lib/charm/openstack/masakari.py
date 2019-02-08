import collections
import socket
import subprocess

import charmhelpers.core.hookenv as hookenv
import charms_openstack.charm
import charms_openstack.ip as os_ip

# import charms_openstack.sdn.odl as odl
# import charms_openstack.sdn.ovs as ovs


class MasakariCharm(charms_openstack.charm.HAOpenStackCharm):

    # Internal name of charm
    service_name = name = 'masakari'

    # First release supported
    release = 'mitaka'

    # List of packages to install for this charm
    packages = ['masakari', 'python-apt']

    api_ports = {
        'masakari': {
            os_ip.PUBLIC: 15868,
            os_ip.ADMIN: 15868,
            os_ip.INTERNAL: 15868,
        }
    }

    service_type = 'masakari'
    default_service = 'masakari'
    services = ['haproxy', 'masakari']

    # Note that the hsm interface is optional - defined in config.yaml
    required_relations = ['shared-db', 'amqp', 'identity-service']

    restart_map = {

        '/etc/masakari/masakari.conf': services,
    }

    ha_resources = ['vips', 'haproxy']

    release_pkg = 'masakari-common'

    package_codenames = {
        'masakari-common': collections.OrderedDict([
            ('2', 'mitaka'),
            ('3', 'newton'),
            ('4', 'ocata'),
        ]),
    }


    sync_cmd = ['congress-db-manage', '--config-file', '/etc/congress/congress.conf', 'upgrade', 'head']

    def get_amqp_credentials(self):
        return ('masakari', 'masakari')

    def get_database_setup(self):
        return [{
            'database': 'masakari',
            'username': 'masakari',
            'hostname': hookenv.unit_private_ip() },]