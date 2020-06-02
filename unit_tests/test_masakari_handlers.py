# Copyright 2019 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

import reactive.masakari_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'amqp.connected',
            'shared-db.connected',
            'identity-service.connected',
            'identity-service.available',  # enables SSL support
            'config.changed',
            'update-status']
        hook_set = {
            'when': {
                'render_config': (
                    'shared-db.available',
                    'identity-service.available',
                    'amqp.available', ),
                'init_db': ('config.rendered', ),
                'cluster_connected': ('ha.connected', )}
        }
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestHandlers(test_utils.PatchHelper):

    def _patch_provide_charm_instance(self):
        masakari_charm = mock.MagicMock()
        self.patch('charms_openstack.charm.provide_charm_instance',
                   name='provide_charm_instance',
                   new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = masakari_charm
        self.provide_charm_instance().__exit__.return_value = None
        return masakari_charm

    def test_render_config(self):
        self.patch('charms.reactive.set_state', name='set_state')
        masakari_charm = self._patch_provide_charm_instance()
        handlers.render_config('keystone', 'shared-db', 'amqp')
        masakari_charm.upgrade_if_available.assert_called_once_with(
            ('keystone', 'shared-db', 'amqp'))
        masakari_charm.render_with_interfaces.assert_called_once_with(
            ('keystone', 'shared-db', 'amqp'))
        masakari_charm.assess_status.assert_called_once_with()
        self.set_state.assert_called_once_with('config.rendered')

    def test_init_db(self):
        masakari_charm = self._patch_provide_charm_instance()
        handlers.init_db()
        masakari_charm.db_sync.assert_called_once_with()

    def test_cluster_connected(self):
        masakari_charm = self._patch_provide_charm_instance()
        handlers.cluster_connected('hacluster')
        masakari_charm.configure_ha_resources.assert_called_once_with(
            'hacluster')
        masakari_charm.assess_status.assert_called_once_with()
