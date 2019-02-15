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

import mock

from omnipath.tests.unit import base


class TestOmniPathFabricAgent(base.TestOmniPathBase):

    def setUp(self):
        super(TestOmniPathFabricAgent, self).setUp()
        self.fabric_agent = self.mech_driver.opafmvf.cli

    def test_fabric_agent_management_command(self):
        with mock.patch.object(self.fabric_agent,
                               "execute_command",
                               return_value=0) as mock_fa:
            self.fabric_agent.osfa_management_commands("reset")
            mock_fa.assert_called_once_with(" opafmvf reset")

    def test_fabric_agent_queries(self):
        with mock.patch.object(self.fabric_agent,
                               "execute_command",
                               return_value=0) as mock_fa:
            command = " opafmvf ismember fake_vf "
            self.fabric_agent.osfa_query_commands("ismember",
                                                  "fake_vf")
            mock_fa.assert_called_once_with(command)
