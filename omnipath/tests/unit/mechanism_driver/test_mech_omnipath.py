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

from oslo_utils import uuidutils

from omnipath.db import api as db_api
from omnipath.tests.unit import base


class TestOmniPathMechanismDriver(base.TestOmniPathBase, base.DBTestCase):

    def setUp(self):
        super(TestOmniPathMechanismDriver, self).setUp()

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
        context.network = fake_net
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

    def test_db_multiple_rows_get(self):
        ctx_net1 = self._get_fake_network_context()
        ctx_net2 = self._get_fake_network_context()
        self.mech_driver.create_network_precommit(ctx_net1)
        self.mech_driver.create_network_precommit(ctx_net2)
        res = db_api.get_all_entries_by_state(ctx_net2, "pending")
        self.assertEqual(2, len(res))
        db_api.update_multiple_rows(ctx_net2, "completed",
                                    [ctx_net1.current['id'],
                                     ctx_net2.current['id']])
        res2 = db_api.get_all_entries_by_state(ctx_net2, "completed")
        self.assertEqual(2, len(res2))
        for row in res2:
            self.assertEqual("completed", row.state)

    def test_all_postcommits(self):
        with mock.patch.object(
            self.mech_driver.omnipath_thread, "set_sync_event") \
                as mock_sync:
            self.mech_driver.create_network_postcommit(mock.ANY)
            self.mech_driver.delete_network_postcommit(mock.ANY)
            self.mech_driver.create_port_postcommit(mock.ANY)
            self.mech_driver.delete_port_postcommit(mock.ANY)
            # call count should be 3 since create_port doesn't set_sync_event
            self.assertEqual(3, mock_sync.call_count)

    @mock.patch('neutron.db.provisioning_blocks.provisioning_complete')
    def test_bind_port(self, mock_pb):
        ctx_port = self._get_fake_port_context()
        ctx_port.segments_to_bind = [{'id': 'fake_segment'}]
        ctx_port.set_binding = mock.Mock()
        with mock.patch.object(
            self.mech_driver.omnipath_thread, "set_sync_event") \
                as mock_bind:
            self.mech_driver.create_port_precommit(ctx_port)
            self.mech_driver.bind_port(ctx_port)
        self.assertTrue(mock_bind.called)
        self.assertTrue(mock_pb.called)
