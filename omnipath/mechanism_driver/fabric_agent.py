# Copyright (c) 2019 Intel Corporation
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

import paramiko

from oslo_config import cfg as config
from oslo_log import log as logging

from omnipath.common import constants
from omnipath.common import omnipath_conf
from omnipath.common import omnipath_exceptions

LOG = logging.getLogger(__name__)
OPA_BINARY = "opafmvf"


class FabricAgentCLI(object):
    def __init__(self):
        self._agent_hostname = None
        self._agent_username = None
        self._agent_key_path = None
        config.CONF.register_opts(omnipath_conf.omnipath_opts,
                                  "ml2_omnipath")

        self._read_config()

        self.client = paramiko.SSHClient()

    def _read_config(self):
        self._agent_hostname = config.CONF.ml2_omnipath.ip_address
        LOG.info("Fabric Agent IP address: %s", self._agent_hostname)
        self._agent_username = config.CONF.ml2_omnipath.username
        self._agent_key_path = config.CONF.ml2_omnipath.ssh_key

    def connect(self):
        try:
            key = paramiko.RSAKey.from_private_key_file(self._agent_key_path)
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self._agent_hostname, port=22,
                username=self._agent_username, pkey=key)
        except omnipath_exceptions.FabricAgentCLIError:
            LOG.error("Error connecting to Omnipath FM")

    def execute_command(self, command):
        self.connect()
        exec_engine = self.client.get_transport().open_session()
        exec_engine.exec_command(command)
        LOG.debug("Command dispatched %s", command)
        exec_status = exec_engine.recv_exit_status()
        self.client.close()
        return exec_status

    def _prepare_command(self, cmd):
        command = ""
        for bit in cmd:
            command = command + " " + bit
        return command

    def osfa_config_commands(self, command, vf_name, *args):
        try:
            if command == constants.OPA_CREATE:
                pkey = "--pkey " + str(args[0])
                cmd = [OPA_BINARY, constants.OPA_CREATE, vf_name, pkey]
            elif command == constants.OPA_DELETE:
                cmd = [OPA_BINARY, constants.OPA_DELETE, vf_name]
            elif command == constants.OPA_ADD:
                cmd = [OPA_BINARY, constants.OPA_ADD, vf_name,
                       "".join(str(x + " ") for x in args).rstrip()]
            elif command == constants.OPA_REMOVE:
                cmd = [OPA_BINARY, constants.OPA_REMOVE, vf_name,
                       "".join(str(x + " ") for x in args).rstrip()]
            else:
                raise omnipath_exceptions.FabricAgentUnknownCommandError
            final_cmd = self._prepare_command(cmd)
            return self.execute_command(final_cmd)
        except omnipath_exceptions.FabricAgentUnknownCommandError:
            LOG.error(command + " not supported in opafmvf CLI")

    def osfa_query_commands(self, command, vf_name, *args):
        try:
            if command == "exist":
                cmd = [OPA_BINARY, "exist", vf_name]
            elif command == constants.OPA_ISMEMBER:
                cmd = [OPA_BINARY, constants.OPA_ISMEMBER, vf_name,
                       "".join(str(x + " ") for x in args).rstrip()]
            elif command == constants.OPA_ISNOTMEMBER:
                cmd = [OPA_BINARY, constants.OPA_ISNOTMEMBER, vf_name,
                       "".join(str(x + " ") for x in args).rstrip()]
            else:
                raise omnipath_exceptions.FabricAgentUnknownCommandError
            final_cmd = self._prepare_command(cmd)
            return self.execute_command(final_cmd)
        except omnipath_exceptions.FabricAgentUnknownCommandError:
            LOG.error(command + " not supported in opafmvf CLI")

    def osfa_management_commands(self, command):
        try:
            if command == "reset":
                cmd = [OPA_BINARY, "reset"]
            elif command == constants.OPA_COMMIT:
                cmd = [OPA_BINARY, constants.OPA_COMMIT, "-f"]
            elif command == constants.OPA_RELOAD:
                cmd = [OPA_BINARY, constants.OPA_RELOAD]
            elif command == constants.OPA_RESTART:
                cmd = [OPA_BINARY, constants.OPA_RESTART]
            elif command == "abort":
                cmd = [OPA_BINARY, "killall -9", OPA_BINARY]
            else:
                raise omnipath_exceptions.FabricAgentUnknownCommandError
            final_cmd = self._prepare_command(cmd)
            return self.execute_command(final_cmd)
        except omnipath_exceptions.FabricAgentUnknownCommandError:
            LOG.error(command + " not supported in opafmvf CLI")


class FabricAgentClient(object):
    def __init__(self):
        self.cli = FabricAgentCLI()

    def get_port_status(self, vf_name, guid):
        """Get status of port

        :param vf_name: Name of the VF
        :param guid: ID of the physical server
        :return: bind status
        """

        query_status = self.cli.osfa_query_commands(
            constants.OPA_ISMEMBER, vf_name, [guid])
        if query_status == 0:
            return "UP"
        else:
            return "DOWN"
