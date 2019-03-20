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

from __future__ import absolute_import
from __future__ import print_function

import mock

import charmhelpers

import charm.openstack.masakari as masakari

import charms_openstack.test_utils as test_utils
import charms_openstack.charm


class Helper(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(masakari.MasakariCharm.release)


class TestMasakariCharm(Helper):

    def _patch_config_and_charm(self, config):
        self.patch_object(charmhelpers.core.hookenv, 'config')

        def cf(key=None):
            if key is not None:
                return config[key]
            return config

        self.config.side_effect = cf
        c = masakari.MasakariCharm()
        return c

    def test_get_amqp_credentials(self):
        c = self._patch_config_and_charm({})
        self.assertEqual(
            c.get_amqp_credentials(),
            ('masakari', 'masakari'))

    def test_get_database_setup(self):
        c = self._patch_config_and_charm({})
        self.assertEqual(
            c.get_database_setup(),
            [{'database': 'masakari', 'username': 'masakari'}])

    def test_public_url(self):
        self.patch_object(charms_openstack.charm.HAOpenStackCharm,
                          'public_url', new_callable=mock.PropertyMock)
        c = self._patch_config_and_charm({})
        self.public_url.return_value = 'http://masakari-public'
        self.assertEqual(
            c.public_url,
            'http://masakari-public/v1/%(tenant_id)s')

    def test_admin_url(self):
        self.patch_object(charms_openstack.charm.HAOpenStackCharm,
                          'admin_url', new_callable=mock.PropertyMock)
        c = self._patch_config_and_charm({})
        self.admin_url.return_value = 'http://masakari-admin'
        self.assertEqual(
            c.admin_url,
            'http://masakari-admin/v1/%(tenant_id)s')

    def test_internal_url(self):
        self.patch_object(charms_openstack.charm.HAOpenStackCharm,
                          'internal_url', new_callable=mock.PropertyMock)
        c = self._patch_config_and_charm({})
        self.internal_url.return_value = 'http://masakari-internal'
        self.assertEqual(
            c.internal_url,
            'http://masakari-internal/v1/%(tenant_id)s')
