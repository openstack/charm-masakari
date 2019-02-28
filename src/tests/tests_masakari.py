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
import time
import uuid

#from keystoneauth1.identity.generic import password as ks_password
from openstack import connection
from openstack import exceptions

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

    def launch_instance(self, instance_key, use_boot_volume=False, vm_name=None):
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
                    'delete_on_termination': True,
                    }]
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


    def test_blah(self):
#         self.masakari_client.create_segment(
#             name='seg1',
#             recovery_method='auto',
#             service_type='COMPUTE')
#         self.masakari_client.create_segment(
#             name='seg2',
#             recovery_method='auto',
#             service_type='COMPUTE')
#         hypervisors = self.nova_client.hypervisors.list()
#         segment_ids = [s.uuid for s in self.masakari_client.segments()] * len(hypervisors)
#         for hypervisor in hypervisors:
#             target_segment = segment_ids.pop()
#             hostname = hypervisor.hypervisor_hostname.split('.')[0]
#             self.masakari_client.create_host(
#                 name=hostname,
#                 segment_id=target_segment,
#                 recovery_method='auto',
#                 control_attributes='SSH',
#                 type='COMPUTE')
         lts = 'bionic'
#         images = openstack_utils.get_images_by_name(self.glance_client, lts)
#         assert len(images) > 0, "Image not found"
#         image = images[0]
         test_vol_name = "zaza{}".format(lts)
#         vol_new = self.cinder_client.volumes.create(
#             name=test_vol_name,
#             imageRef=image.id,
#             size=3)
#         openstack_utils.resource_reaches_status(
#             self.cinder_client.volumes,
#             vol_new.id,
#             expected_status='available')
#         test_vol = self.cinder_client.volumes.find(name=test_vol_name)
#         self.cinder_client.volumes.set_bootable(test_vol, True)
#         self.launch_instance('bionic', use_boot_volume=True)
         vm_name = '20190228090550'
#         server = self.nova_client.servers.find(name=vm_name)
#         guest_hypervisor = getattr(server, 'OS-EXT-SRV-ATTR:host')
#         hypervisor_machine_number = guest_hypervisor.split('-')[-1]         
#         unit = [u.entity_id
#                 for u in zaza.model.get_units(application_name='nova-compute')
#                 if u.data['machine-id'] == hypervisor_machine_number][0]
#         zaza.model.run_on_unit(unit, command='shutdown -h now', model_name=self.model_name)

         server = self.nova_client.servers.find(name=vm_name)
         guest_hypervisor = getattr(server, 'OS-EXT-SRV-ATTR:host')
         print("{} {}".format(guest_hypervisor, server.status))

         print(unit)
         assert list(self.masakari_client.segments()) == ['bob'], "{}".format(list(self.masakari_client.segments()))


#    def test_cinder_config(self):
#        logging.info('ns5')
#        expected_contents = {
#            'cinder-ns5': {
#                'volume_driver': [
#                    'cinder.volume.drivers.nexenta.ns5.nfs.NexentaNfsDriver'],
#                'volume_backend_name': ['cinder-ns5'],
#                'nexenta_rest_port': ['0'],
#                'nexenta_user': ['admin'],
#                'nas_share_path': ['tank/data']}}
#
#        zaza.model.run_on_leader(
#            'cinder',
#            'sudo cp /etc/cinder/cinder.conf /tmp/',
#            model_name=self.model_name)
#        zaza.model.block_until_oslo_config_entries_match(
#            'cinder',
#            '/tmp/cinder.conf',
#            expected_contents,
#            model_name=self.model_name,
#            timeout=2)
#
#    def create_volume(self):
#        test_vol_name = "zaza{}".format(uuid.uuid1().fields[0])
#        vol_new = self.cinder_client.volumes.create(
#            name=test_vol_name,
#            size=1)
#        openstack_utils.resource_reaches_status(
#            self.cinder_client.volumes,
#            vol_new.id,
#            expected_status='available')
#        test_vol = self.cinder_client.volumes.find(name=test_vol_name)
#        self.assertEqual(
#            getattr(test_vol, 'os-vol-host-attr:host').split('#')[0],
#            'cinder@cinder-ns5')
#        return test_vol_name
#
#    def test_create_volume(self):
#        volume_name = self.create_volume()
#        volume = self.cinder_client.volumes.find(name=volume_name)
#        self.cinder_client.volumes.delete(volume)
#
#    def test_attatch_volume_to_guest(self):
#        volume_name = self.create_volume()
#        volume = self.cinder_client.volumes.find(name=volume_name)
#        servers = self.nova_client.servers.findall()
#        assert len(servers) > 0, "No server found to run attach test"
#        server = servers[0]
#        self.nova_client.volumes.create_server_volume(server.id, volume.id)
#        attached_volumes = self.nova_client.volumes.get_server_volumes(
#            server.id)
#        assert len(attached_volumes) > 0, "No attached volumes found"
#        assert attached_volumes[0].id == volume.id, ("Error matching attached "
#                                                     "volume")
#        print(openstack_utils.get_private_key(nova_utils.KEYPAIR_NAME))
