# Copyright 2019 Intel Corporation
# All Rights Reserved.
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


from neutron_lib.plugins import directory
from oslo_config import cfg

from neutron.plugins.ml2.drivers import type_flat  # noqa
from neutron.tests.unit.plugins.ml2 import test_plugin
from neutron.tests.unit.testlib_api import SqlTestCaseLight
from neutron_lib import context

from omnipath.db import models


MECH_OMNIPATH = 'omnipath_mech'


class DBTestCase(SqlTestCaseLight):

    def setUp(self):
        super(DBTestCase, self).setUp()
        self.db_context = context.get_admin_context()
        self.session = self.db_context.session

    def tearDown(self):
        super(DBTestCase, self).tearDown()
        self.session.query(models.OmniPathRevisionNumbers).delete()


class TestOmniPathBase(test_plugin.Ml2PluginV2TestCase):

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
        super(TestOmniPathBase, self).setUp()
        mechmanager = directory.get_plugin().mechanism_manager
        self.mech_driver = mechmanager.mech_drivers[MECH_OMNIPATH].obj
