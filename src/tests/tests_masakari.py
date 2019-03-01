#!/usr/bin/env python3

# Copyright 2019 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Encapsulate cinder-ns5 testing."""

import logging
import tenacity
import time

from openstack import connection

import zaza.model
import zaza.charm_tests.test_utils as test_utils
import zaza.utilities.openstack as openstack_utils
import zaza.charm_tests.nova.utils as nova_utils


class MasakariTest(test_utils.OpenStackBaseTest):
    """Encapsulate NS5 tests."""

    @classmethod
    def setUpClass(cls):
        """Run class setup for running tests."""
        super(MasakariTest, cls).setUpClass()
        cls.keystone_session = openstack_utils.get_overcloud_keystone_session()
        cls.model_name = zaza.model.get_juju_model()
        cls.cinder_client = openstack_utils.get_cinder_session_client(
            cls.keystone_session)
        cls.nova_client = openstack_utils.get_nova_session_client(
            cls.keystone_session)
        cls.glance_client = openstack_utils.get_glance_session_client(
            cls.keystone_session)
        cls.neutron_client = openstack_utils.get_neutron_session_client(
            cls.keystone_session)

        conn = connection.Connection(session=cls.keystone_session,
                                     interface='public',
                                     region_name='RegionOne')
        cls.masakari_client = conn.instance_ha

    def launch_instance(self, instance_key, use_boot_volume=False,
                        vm_name=None):
        """Launch an instance.

        :param instance_key: Key to collect associated config data with.
        :type instance_key: str
        """
        # Collect resource information.
        vm_name = vm_name or time.strftime("%Y%m%d%H%M%S")
        image = self.nova_client.glance.find_image(
            instance_key)
        flavor = self.nova_client.flavors.find(
            name='m1.small')
        net = self.neutron_client.find_resource("network", "private")
        nics = [{'net-id': net.get('id')}]

        if use_boot_volume:
            bdmv2 = [{
                'boot_index': '0',
                'uuid': image.id,
                'source_type': 'image',
                'volume_size': flavor.disk,
                'destination_type': 'volume',
                'delete_on_termination': True}]
            image = None

        # Launch instance.
        logging.info('Launching instance {}'.format(vm_name))
        instance = self.nova_client.servers.create(
            name=vm_name,
            image=image,
            block_device_mapping_v2=bdmv2,
            flavor=flavor,
            key_name=nova_utils.KEYPAIR_NAME,
            nics=nics)

        # Test Instance is ready.
        logging.info('Checking instance is active')
        openstack_utils.resource_reaches_status(
            self.nova_client.servers,
            instance.id,
            expected_status='ACTIVE')

        logging.info('Checking cloud init is complete')
        openstack_utils.cloud_init_complete(
            self.nova_client,
            instance.id,
            'finished at')
        port = openstack_utils.get_ports_from_device_id(
            self.neutron_client,
            instance.id)[0]
        logging.info('Assigning floating ip.')
        ip = openstack_utils.create_floating_ip(
            self.neutron_client,
            "ext_net",
            port=port)['floating_ip_address']
        logging.info('Assigned floating IP {} to {}'.format(ip, vm_name))
        openstack_utils.ping_response(ip)

        # Check ssh'ing to instance.
#        logging.info('Testing ssh access.')
#        openstack_utils.ssh_test(
#            username='ubuntu',
#            ip=ip,
#            vm_name=vm_name,
#            password=None,
#            privkey=openstack_utils.get_private_key(nova_utils.KEYPAIR_NAME))

    def configure(self):
        try:
            self.masakari_client.create_segment(
                name='seg1',
                recovery_method='auto',
                service_type='COMPUTE')
            hypervisors = self.nova_client.hypervisors.list()
            segment_ids = [s.uuid for s in self.masakari_client.segments()]
            segment_ids = segment_ids * len(hypervisors)
            for hypervisor in hypervisors:
                target_segment = segment_ids.pop()
                hostname = hypervisor.hypervisor_hostname.split('.')[0]
                self.masakari_client.create_host(
                    name=hostname,
                    segment_id=target_segment,
                    recovery_method='auto',
                    control_attributes='SSH',
                    type='COMPUTE')
        except:
            pass

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, max=60),
                    reraise=True, stop=tenacity.stop_after_attempt(80))
    def wait_for_server_migration(self, vm_name, original_hypervisor):
        server = self.nova_client.servers.find(name=vm_name)
        current_hypervisor = getattr(server, 'OS-EXT-SRV-ATTR:host')
        logging.info('{} is on {} in state {}'.format(
            vm_name,
            current_hypervisor,
            server.status))
        assert (original_hypervisor != current_hypervisor and
                server.status == 'ACTIVE')
        logging.info('SUCCESS {} has migrated to {}'.format(
            vm_name,
            current_hypervisor))

    def svc_control(self, unit_name, action, services):
        logging.info('{} {} on {}'.format(action.title(), services, unit_name))
        cmds = []
        for svc in services:
            cmds.append("systemctl {} {}".format(action, svc))
        zaza.model.run_on_unit(
            unit_name, command=';'.join(cmds),
            model_name=self.model_name)

    def enable_the_things(self):
        logging.info("Enabling all the things")
        # Start corosync et al
        for u in zaza.model.get_units(application_name='nova-compute'):
            self.svc_control(
                u.entity_id,
                'start',
                ['corosync', 'pacemaker', 'nova-compute'])

        # Enable nova-compute in nova
        for svc in self.nova_client.services.list():
            if svc.status == 'disabled':
                logging.info("Enabling {} on {}".format(svc.binary, svc.host))
                self.nova_client.services.enable(svc.host, svc.binary)

        # Enable nova-compute in masakari
        for segment in self.masakari_client.segments():
            for host in self.masakari_client.hosts(segment_id=segment.uuid):
                if host.on_maintenance:
                    logging.info("Removing maintenance mode from masakari "
                                 "host {}".format(host.uuid))
                    self.masakari_client.update_host(
                        host.uuid,
                        segment_id=segment.uuid,
                        **{'on_maintenance': False})

    def test_instance_failover(self):
        self.configure()
        # Launch guest
        vm_name = 'zaza_test_instance_failover'
        try:
            server = self.nova_client.servers.find(name=vm_name)
            logging.info('Found existing guest')
        except:
            logging.info('Launching new guest')
            self.launch_instance(
                'bionic',
                use_boot_volume=True,
                vm_name=vm_name)
            server = self.nova_client.servers.find(name=vm_name)
        logging.info('Finding hosting hypervisor')
        server = self.nova_client.servers.find(name=vm_name)
        current_hypervisor = getattr(server, 'OS-EXT-SRV-ATTR:host')

        logging.info('Simulate compute node shutdown')
        server = self.nova_client.servers.find(name=vm_name)
        guest_hypervisor = getattr(server, 'OS-EXT-SRV-ATTR:host')
        hypervisor_machine_number = guest_hypervisor.split('-')[-1]
        unit_name = [
            u.entity_id
            for u in zaza.model.get_units(application_name='nova-compute')
            if u.data['machine-id'] == hypervisor_machine_number][0]

        # Simulate shutdown
        self.svc_control(
            unit_name,
            'stop',
            ['corosync', 'pacemaker', 'nova-compute'])

        # Wait for instance move
        self.wait_for_server_migration(vm_name, current_hypervisor)

        # Bring things back
        self.enable_the_things()
