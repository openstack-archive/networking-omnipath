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


from neutron_lib.api.definitions import portbindings
from neutron_lib.callbacks import resources
from neutron_lib import context as nl_context
from neutron_lib.plugins.ml2 import api
from oslo_log import log as logging

from neutron.db import provisioning_blocks
from neutron.objects import ports

from omnipath.common import constants as op_const
from omnipath.db import api as opadbapi
from omnipath.mechanism_driver import fabric_agent
from omnipath import omnipath_thread as ojournal
from omnipath import omnipath_worker

LOG = logging.getLogger(__name__)

# TODO(manjeets) use this parameter from config
sync_time = 10


class OmnipathMechanismDriver(api.MechanismDriver):
    def initialize(self):
        self.opafmvf = fabric_agent.FabricAgentClient()
        # Runs sync() every "sync_time" seconds
        self.omnipath_thread = ojournal.OmniPathThread(
            fabric_cli=self.opafmvf.cli)
        self.omnipath_thread.start()
        self.supported_vnic_types = [portbindings.VNIC_NORMAL,
                                     portbindings.VNIC_DIRECT,
                                     "baremetal"]

    def get_workers(self):
        workers = [omnipath_worker.OmniPathPeriodicProcessor()]
        return workers

    @staticmethod
    def update_port_status_db(context, port_id, status):
        """Update Ports in DB

        :param port_id: ID of port to update status
        :param status: Status of the port
        :return: Updated Port Object
        """
        ctx = context.get_admin_context()
        return ports.Port.update_object(
            ctx, {'status': status}, port_id=port_id)

    @staticmethod
    def _is_port_supported(port):
        """Return whether a port is supported by this driver.

        Ports supported by this driver have a VNIC type of 'baremetal'.
        :param port: The port to check
        :returns: Whether the port is supported by the NGS driver
        """
        vnic_type = port[portbindings.VNIC_TYPE]
        return vnic_type == portbindings.VNIC_BAREMETAL

    def create_network_precommit(self, context):
        """Allocate resources for a new network.

        :param context: NetworkContext instance describing the new
        network.

        Create a new network, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        # (manjeets) add the revision number logic here.
        net = context.current
        res_id = net['id']
        res_type = "network"
        net['operation'] = op_const.OPA_CREATE
        net['op_type'] = "config"
        opadbapi.record_pending_entry(
            context._plugin_context, res_id, res_type, net)

    def create_network_postcommit(self, context):
        """Create a network.

        :param context: NetworkContext instance describing the new
        network.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.
        """
        self.omnipath_thread.set_sync_event()

    def update_network_precommit(self, context):
        """Update resources of a network.

        :param context: NetworkContext instance describing the new
        state of the network, as well as the original state prior
        to the update_network call.

        Update values of a network, updating the associated resources
        in the database. Called inside transaction context on session.
        Raising an exception will result in rollback of the
        transaction.

        update_network_precommit is called for all changes to the
        network state. It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        return

    def update_network_postcommit(self, context):
        """Update a network.

        :param context: NetworkContext instance describing the new
        state of the network, as well as the original state prior
        to the update_network call.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.

        update_network_postcommit is called for all changes to the
        network state.  It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        # Is Network update required for OPA?
        return

    def delete_network_precommit(self, context):
        """Delete resources for a network.

        :param context: NetworkContext instance describing the current
        state of the network, prior to the call to delete it.

        Delete network resources previously allocated by this
        mechanism driver for a network. Called inside transaction
        context on session. Runtime errors are not expected, but
        raising an exception will result in rollback of the
        transaction.
        """
        net = context.current
        res_id = net['id']
        res_type = "network"
        net['operation'] = op_const.OPA_DELETE
        net['op_type'] = "config"
        row = opadbapi.get_resource_row(context._plugin_context,
                                        res_id, res_type)
        if not row:
            return
        row.data = net
        row.state = 'pending'
        context._plugin_context.session.merge(row)

    def delete_network_postcommit(self, context):
        """Delete a network.

        :param context: NetworkContext instance describing the current
        state of the network, prior to the call to delete it.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        self.omnipath_thread.set_sync_event()

    def create_subnet_precommit(self, context):
        """Allocate resources for a new subnet.

        :param context: SubnetContext instance describing the new
        subnet.
        rt = context.current
        device_id = port['device_id']
        device_owner = port['device_owner']
        Create a new subnet, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        return

    def create_subnet_postcommit(self, context):
        """Create a subnet.

        :param context: SubnetContext instance describing the new
        subnet.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.
        """
        return

    def update_subnet_precommit(self, context):
        """Update resources of a subnet.

        :param context: SubnetContext instance describing the new
        state of the subnet, as well as the original state prior
        to the update_subnet call.

        Update values of a subnet, updating the associated resources
        in the database. Called inside transaction context on session.
        Raising an exception will result in rollback of the
        transaction.

        update_subnet_precommit is called for all changes to the
        subnet state. It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        return

    def update_subnet_postcommit(self, context):
        """Update a subnet.

        :param context: SubnetContext instance describing the new
        state of the subnet, as well as the original state prior
        to the update_subnet call.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.

        update_subnet_postcommit is called for all changes to the
        subnet state.  It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        return

    def delete_subnet_precommit(self, context):
        """Delete resources for a subnet.

        :param context: SubnetContext instance describing the current
        state of the subnet, prior to the call to delete it.

        Delete subnet resources previously allocated by this
        mechanism driver for a subnet. Called inside transaction
        context on session. Runtime errors are not expected, but
        raising an exception will result in rollback of the
        transaction.
        """
        return

    def delete_subnet_postcommit(self, context):
        """Delete a subnet.

        :param context: SubnetContext instance describing the current
        state of the subnet, prior to the call to delete it.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        return

    def create_port_precommit(self, context):
        """Allocate resources for a new port.

        :param context: PortContext instance describing the port.

        Create a new port, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        port = context.current
        port['operation'] = op_const.OPA_CREATE
        port['op_type'] = "config"
        profile = context.current.get(portbindings.PROFILE)
        node_guid = profile.get('guid')
        if not node_guid:
            # port doesn't belong to this backend
            return
        port['guid'] = node_guid
        opadbapi.record_pending_entry(context._plugin_context,
                                      port['id'], "port", port,
                                      state='waiting')

    def create_port_postcommit(self, context):
        """Create a port.

        :param context: PortContext instance describing the port.

        Called after the transaction completes. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance.  Raising an exception will
        result in the deletion of the resource.
        """
        return

    def update_port_precommit(self, context):
        """Update resources of a port.

        :param context: PortContext instance describing the new
        state of the port, as well as the original state prior
        to the update_port call.

        Called inside transaction context on session to complete a
        port update as defined by this mechanism driver. Raising an
        exception will result in rollback of the transaction.

        update_port_precommit is called for all changes to the port
        state. It is up to the mechanism driver to ignore state or
        state changes that it does not know or care about.
        """
        port = context.current
        if 'dhcp' in port['device_owner']:
            return

    def update_port_postcommit(self, context):
        """Update a port.

        :param context: PortContext instance describing the new
        state of the port, as well as the original state prior
        to the update_port call.

        Called after the transaction completes. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance.  Raising an exception will
        result in the deletion of the resource.

        update_port_postcommit is called for all changes to the port
        state. It is up to the mechanism driver to ignore state or
        state changes that it does not know or care about.
        """
        # TODO(manjeets) update if needed
        return

    def _unplug_port_from_network(self, context):
        self.delete_port_precommit(context)
        self.omnipath_thread.set_sync_event()

    def delete_port_precommit(self, context):
        """Delete resources of a port.

        :param context: PortContext instance describing the current
        state of the port, prior to the call to delete it.

        Called inside transaction context on session. Runtime errors
        are not expected, but raising an exception will result in
        rollback of the transaction.
        """
        port = context.current
        port_row = opadbapi.get_resource_row(
            context._plugin_context, port['id'], "port")
        portdict = port_row.get("data") if port_row else None
        node_guid = portdict.get('guid') if portdict else None
        if not port_row or not node_guid:
            return
        port["operation"] = op_const.OPA_DELETE
        port["guid"] = node_guid
        port_row.state = 'waiting'
        port_row.data = port
        context._plugin_context.session.merge(port_row)

    def delete_port_postcommit(self, context):
        """Delete a port.

        :param context: PortContext instance describing the current
        state of the port, prior to the call to delete it.

        Called after the transaction completes. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance.  Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        # Remove port from DB. Once removed, it will be
        # synced every "sync_time" as done in  __init__
        self.omnipath_thread.set_sync_event()

    def bind_port(self, context):
        """Attempt to bind a port.

        :param context: PortContext instance describing the port

        This method is called outside any transaction to attempt to
        establish a port binding using this mechanism driver. Bindings
        may be created at each of multiple levels of a hierarchical
        network, and are established from the top level downward. At
        each level, the mechanism driver determines whether it can
        bind to any of the network segments in the
        context.segments_to_bind property, based on the value of the
        context.host property, any relevant port or network
        attributes, and its own knowledge of the network topology. At
        the top level, context.segments_to_bind contains the static
        segments of the port's network. At each lower level of
        binding, it contains static or dynamic segments supplied by
        the driver that bound at the level above. If the driver is
        able to complete the binding of the port to any segment in
        context.segments_to_bind, it must call context.set_binding
        with the binding details. If it can partially bind the port,
        it must call context.continue_binding with the network
        segments to be used to bind at the next lower level.

        If the binding results are committed after bind_port returns,
        they will be seen by all mechanism drivers as
        update_port_precommit and update_port_postcommit calls. But if
        some other thread or process concurrently binds or updates the
        port, these binding results will not be committed, and
        update_port_precommit and update_port_postcommit will not be
        called on the mechanism drivers with these results. Because
        binding results can be discarded rather than committed,
        drivers should avoid making persistent state changes in
        bind_port, or else must ensure that such state changes are
        eventually cleaned up.

        Implementing this method explicitly declares the mechanism
        driver as having the intention to bind ports. This is inspected
        by the QoS service to identify the available QoS rules you
        can use with ports.
        """
        port_data = context.current
        port = opadbapi.get_resource_row(context._plugin_context,
                                         port_data['id'], "port")
        portdict = port.get("data") if port else None
        node_guid = portdict.get('guid') if portdict else None
        if not port or not node_guid:
            return
        port_data["operation"] = "bind"
        port_data['guid'] = node_guid
        port.data = port_data
        context._plugin_context.session.merge(port)
        net_id = context.network.current['id']
        LOG.debug("Attempting to bind port %(port)s on "
                  "network %(network)s",
                  {'port': context.current['id'],
                   'network': net_id})
        segment = context.segments_to_bind[0]
        if not segment:
            LOG.debug("Port Binding error no valid segments to bind")
            return
        context.set_binding(segment[api.ID], "PKEY", {}, status='ACTIVE')
        provisioning_blocks.provisioning_complete(
            nl_context.get_admin_context(),
            port.data['id'], resources.PORT,
            provisioning_blocks.L2_AGENT_ENTITY)
        self.omnipath_thread.set_sync_event()
