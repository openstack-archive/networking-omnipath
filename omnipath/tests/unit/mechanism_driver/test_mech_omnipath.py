#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import random

import mock

from neutron_lib.plugins import directory
from oslo_config import cfg
from oslo_utils import uuidutils

from neutron.plugins.ml2.drivers import type_flat  # noqa
from neutron.tests.unit.plugins.ml2 import test_plugin

from omnipath.db import api as db_api
from omnipath.tests.unit import db_base


MECH_OMNIPATH = 'omnipath_mech'


class TestOmniPathMechanismDriver(test_plugin.Ml2PluginV2TestCase,
                                  db_base.DBTestCase):

    _mechanism_drivers = [MECH_OMNIPATH]
    _extension_drivers = ['port_security']

    def setUp(self):
        cfg.CONF.set_override('extension_drivers',
                              self._extension_drivers,
                              group='ml2')
        cfg.CONF.set_override('tenant_network_types',
                              ['vlan'],
                              group='ml2')
        cfg.CONF.set_override('flat_networks',
                              ['public', 'mynet'],
                              group='ml2_type_flat')
        cfg.CONF.set_override('network_vlan_ranges',
                              ['mynet:2:2000'],
                              group='ml2_type_vlan')
        super(TestOmniPathMechanismDriver, self).setUp()
        mechmanager = directory.get_plugin().mechanism_manager
        self.mech_driver = mechmanager.mech_drivers[MECH_OMNIPATH].obj

    def _get_fake_network_context(self):
        current = {'status': 'ACTIVE',
                   'subnets': [],
                   'name': 'net1',
                   'provider:physical_network': None,
                   'admin_state_up': True,
                   'tenant_id': 'test-tenant',
                   'provider:network_type': 'vlan',
                   'shared': False,
                   'id': uuidutils.generate_uuid(),
                   'provider:segmentation_id': random.randint(2, 2000)}
        context = mock.Mock(current=current)
        context.session = self.session
        context._plugin_context = self.db_context
        return context

    def _get_fake_port_context(self):
        fake_net = self._get_fake_network_context()
        current = {'status': 'DOWN',
                   'binding:host_id': '',
                   'allowed_address_pairs': [],
                   'device_owner': 'fake_owner',
                   'binding:profile': {'guid': 'fake_guid'},
                   'fixed_ips': [{
                       'subnet_id': uuidutils.generate_uuid()}],
                   'id': uuidutils.generate_uuid(),
                   'device_id': 'fake_device',
                   'name': '',
                   'admin_state_up': True,
                   'network_id': fake_net.current['id'],
                   'tenant_id': fake_net.current['tenant_id'],
                   'binding:vif_details': {},
                   'binding:vnic_type': 'baremetal',
                   'binding:vif_type': 'unbound',
                   'mac_address': 'fake_mac'}
        context = mock.Mock(current=current)
        context.session = self.session
        context._plugin_context = self.db_context
        return context

    def _assert_resource_row(self, context, res_op, res_type):
        result = db_api.get_resource_row(context, context.current['id'],
                                         res_type)
        self.assertEqual(result.data, context.current)
        self.assertEqual(result.data['operation'], res_op)

    def test_network_create_precommit(self):
        context = self._get_fake_network_context()
        self.mech_driver.create_network_precommit(context)
        self._assert_resource_row(context, "create", "network")

    def test_network_delete_precommit(self):
        context = self._get_fake_network_context()
        self.mech_driver.create_network_precommit(context)
        self.mech_driver.delete_network_precommit(context)
        self._assert_resource_row(context, "delete", "network")

    def test_port_create_precommit(self):
        context = self._get_fake_port_context()
        self.mech_driver.create_port_precommit(context)
        self._assert_resource_row(context, "create", "port")

    def test_port_delete_precommit(self):
        context = self._get_fake_port_context()
        self.mech_driver.create_port_precommit(context)
        self.mech_driver.delete_port_precommit(context)
        self._assert_resource_row(context, "delete", "port")

    def test__is_port_supported(self):
        context = self._get_fake_port_context()
        is_supported = self.mech_driver._is_port_supported(context.current)
        self.assertTrue(is_supported)

    def test__is_port_supported_false(self):
        context = self._get_fake_port_context()
        context.current['binding:vnic_type'] = 'not_baremetal'
        is_supported = self.mech_driver._is_port_supported(context.current)
        self.assertFalse(is_supported)
