import collections

import charms_openstack.charm
import charms_openstack.ip as os_ip

MASAKARI_WSGI_CONF = '/etc/apache2/sites-enabled/masakari-api.conf'

charms_openstack.charm.use_defaults('charm.default-select-release')


class MasakariCharm(charms_openstack.charm.HAOpenStackCharm):

    # Internal name of charm
    service_name = name = 'masakari'

    # First release supported
    release = 'rocky'

    # List of packages to install for this charm
    packages = ['masakari-api', 'masakari-engine', 'python-apt']

    api_ports = {
        'masakari': {
            os_ip.PUBLIC: 15868,
            os_ip.ADMIN: 15868,
            os_ip.INTERNAL: 15868,
        }
    }

    group = 'masakari'
    service_type = 'masakari'
    default_service = 'masakari'
    services = ['haproxy', 'apache2', 'masakari-engine']

    required_relations = ['shared-db', 'amqp', 'identity-service']

    restart_map = {
        '/etc/masakari/masakari.conf': services,
        MASAKARI_WSGI_CONF: services,
    }

    ha_resources = ['vips', 'haproxy', 'dnsha']

    release_pkg = 'masakari-api'

    package_codenames = {
        'masakari-api': collections.OrderedDict([
            ('2', 'mitaka'),
            ('3', 'newton'),
            ('4', 'ocata'),
            ('5', 'pike'),
            ('6', 'rocky'),
            ('7', 'stein'),
        ]),
    }

    sync_cmd = ['masakari-manage', '--config-file',
                '/etc/masakari/masakari.conf', 'db', 'sync']

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
