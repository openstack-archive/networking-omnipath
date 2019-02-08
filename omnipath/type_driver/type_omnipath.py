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

import collections
import sys

from neutron_lib import context
from neutron_lib.db import api as lib_db_api
from neutron_lib import exceptions as exc
from neutron_lib.plugins.ml2 import api
from oslo_config import cfg as config
from oslo_log import log
from six import moves

from neutron._i18n import _
from neutron.db import api as db_api
from neutron.plugins.ml2.drivers import helpers

from omnipath.common import omnipath_conf
from omnipath.common import omnipath_exceptions
from omnipath.object import omnipathallocation as pkeyalloc


LOG = log.getLogger(__name__)


class OmnipathTypeDriver(helpers.SegmentTypeDriver):
    """Manage state for Omnipath networks with ML2."""

    def __init__(self):
        super(OmnipathTypeDriver, self).__init__(
            pkeyalloc.OmniPathAllocation)
        config.CONF.register_opts(omnipath_conf.omnipath_opts,
                                  "ml2_omnipath")
        self._parse_network_omnipath_ranges()

    def get_type(self):
        return "pkey"

    def _parse_network_omnipath_ranges(self):
        """Read the config file for setting the range of Omnipath pkeys"""
        try:
            self.network_omnipath_ranges = self._parse_omnipath_ranges(
                config.CONF.ml2_omnipath.pkey_ranges)
        except Exception:
            LOG.exception("Failed to parse network_omnipath_ranges. "
                          "Service terminated!")
            sys.exit(1)
        LOG.info("Network Omnipath ranges: %s", self.network_omnipath_ranges)

    def _get_valid_pkey(self, pkey):
        # Implement reserve pkey logic here
        pass

    @lib_db_api.retry_db_errors
    def _sync_omnipath_allocations(self):
        ctx = context.get_admin_context()
        with db_api.context_manager.writer.using(ctx):
            # get existing allocations for all physical networks
            allocations = dict()
            allocs = pkeyalloc.OmniPathAllocation.get_objects(ctx)
            for alloc in allocs:
                if alloc.physical_network not in allocations:
                    allocations[alloc.physical_network] = list()
                allocations[alloc.physical_network].append(alloc)

            # process pkey ranges for each configured physical network
            for (physical_network,
                 omnipath_ranges) in self.network_omnipath_ranges.items():
                # determine current configured allocatable pkey for
                # this physical network
                omnipath_pkeys = set()

                for pkey_min, pkey_max in omnipath_ranges:
                    omnipath_pkeys |= set(moves.range(pkey_min, pkey_max + 1))

                # remove from table unallocated pkeys not currently
                # allocatable
                if physical_network in allocations:
                    for alloc in allocations[physical_network]:
                        try:
                            # see if pkey is allocatable
                            omnipath_pkeys.remove(alloc.pkey)
                        except KeyError:
                            # it's not allocatable, so check if its allocated
                            if not alloc.allocated:
                                # it's not, so remove it from table
                                LOG.debug("Removing pkey %(pkey)s on "
                                          "physical network "
                                          "%(physical_network)s from pool",
                                          {'pkey': alloc.pkey,
                                           'physical_network':
                                               physical_network})
                                # This UPDATE WHERE statement blocks anyone
                                # from concurrently changing the allocation
                                # values to True while our transaction is
                                # open so we don't accidentally delete
                                # allocated segments. If someone has already
                                # allocated, update_objects will return 0 so we
                                # don't delete.
                                if pkeyalloc.OmniPathAllocation.update_objects(
                                        ctx, values={'allocated': False},
                                        allocated=False, pkey=alloc.pkey,
                                        physical_network=physical_network):
                                    alloc.delete()
                    del allocations[physical_network]

                # add missing allocatable pkeys to table
                for pkey in sorted(omnipath_pkeys):
                    alloc = pkeyalloc.OmniPathAllocation(
                        ctx,
                        physical_network=physical_network,
                        pkey=pkey, allocated=False)
                    alloc.create()

            # remove from table unallocated pkeys for any unconfigured
            # physical networks
            for allocs in allocations.values():
                for alloc in allocs:
                    if not alloc.allocated:
                        LOG.debug("Removing pkey %(pkey)s on physical "
                                  "network %(physical_network)s from pool",
                                  {'pkey': alloc.pkey,
                                   'physical_network':
                                       alloc.physical_network})
                        alloc.delete()

    def initialize(self):
        self._sync_omnipath_allocations()
        LOG.info("OmnipathTypeDriver initialization complete")

    def is_partial_segment(self, segment):
        return segment.get(api.SEGMENTATION_ID) is None

    # Provider network in Omnipath?
    def validate_provider_segment(self, segment):
        physical_network = segment.get(api.PHYSICAL_NETWORK)
        segmentation_id = segment.get(api.SEGMENTATION_ID)
        if physical_network:
            if physical_network not in self.network_omnipath_ranges:
                msg = (_("physical_network '%s' unknown "
                         "for Omnipath provider network") % physical_network)
                raise exc.InvalidInput(error_message=msg)
            if segmentation_id:
                if not self.is_valid_omnipath_pkey(segmentation_id):
                    msg = (_("segmentation_id not valid"))
                    raise exc.InvalidInput(error_message=msg)
            else:
                if not self.network_omnipath_ranges.get(physical_network):
                    msg = (_("Physical network %s requires segmentation_id "
                             "to be specified when creating a provider "
                             "network") % physical_network)
                    raise exc.InvalidInput(error_message=msg)
        elif segmentation_id:
            msg = _("segmentation_id requires physical_network for Omnipath "
                    "provider network")
            raise exc.InvalidInput(error_message=msg)

        for key, value in segment.items():
            if value and key not in [api.NETWORK_TYPE,
                                     api.PHYSICAL_NETWORK,
                                     api.SEGMENTATION_ID]:
                msg = _("%s prohibited for Omnipath provider network") % key
                raise exc.InvalidInput(error_message=msg)

    def reserve_provider_segment(self, context, segment):
        filters = {}
        physical_network = segment.get(api.PHYSICAL_NETWORK)
        if physical_network is not None:
            filters['physical_network'] = physical_network
            pkey = segment.get(api.SEGMENTATION_ID)
            if pkey is not None:
                filters['pkey'] = pkey

        if self.is_partial_segment(segment):
            alloc = self.allocate_partially_specified_segment(
                context, **filters)
            if not alloc:
                raise exc.NoNetworkAvailable()
        else:
            alloc = self.allocate_fully_specified_segment(
                context, **filters)
            if not alloc:
                raise omnipath_exceptions.OmnipathPkeyInUse(**filters)

        return {api.NETWORK_TYPE: "pkey",
                api.PHYSICAL_NETWORK: alloc.physical_network,
                api.SEGMENTATION_ID: alloc.pkey,
                api.MTU: self.get_mtu(alloc.physical_network)}

    def allocate_tenant_segment(self, context):
        for physnet in self.network_omnipath_ranges:
            alloc = self.allocate_partially_specified_segment(
                context, physical_network=physnet)
            if alloc:
                break
        else:
            return
        return {api.NETWORK_TYPE: "pkey",
                api.PHYSICAL_NETWORK: alloc.physical_network,
                api.SEGMENTATION_ID: alloc.pkey,
                api.MTU: self.get_mtu(alloc.physical_network)}

    def release_segment(self, context, segment):
        physical_network = segment[api.PHYSICAL_NETWORK]
        pkey = segment[api.SEGMENTATION_ID]

        ranges = self.network_omnipath_ranges.get(physical_network, [])
        inside = any(lo <= pkey <= hi for lo, hi in ranges)
        count = False

        with db_api.context_manager.writer.using(context):
            alloc = pkeyalloc.OmniPathAllocation.get_object(
                context, physical_network=physical_network, pkey=pkey)
            if alloc:
                if inside and alloc.allocated:
                    count = True
                    alloc.allocated = False
                    alloc.update()
                    LOG.debug("Releasing pkey %(pkey)s on physical "
                              "network %(physical_network)s to pool",
                              {'pkey': pkey,
                               'physical_network': physical_network})
                else:
                    count = True
                    alloc.delete()
                    LOG.debug("Releasing pkey %(pkey)s on physical "
                              "network %(physical_network)s outside pool",
                              {'pkey': pkey,
                               'physical_network': physical_network})

        if not count:
            LOG.warning("No pkey %(pkey)s found on physical "
                        "network %(physical_network)s",
                        {'pkey': pkey,
                         'physical_network': physical_network})

    def get_mtu(self, physical_network):
        seg_mtu = super(OmnipathTypeDriver, self).get_mtu()
        mtu = []
        if seg_mtu > 0:
            mtu.append(seg_mtu)
        if physical_network in self.physnet_mtus:
            mtu.append(int(self.physnet_mtus[physical_network]))
        return min(mtu) if mtu else 0

    def _parse_omnipath_ranges(self, network_omnipath_ranges_cfg_entries):
        networks = collections.OrderedDict()
        for entry in network_omnipath_ranges_cfg_entries:
            network, pkey_range = self._parse_network_pkey_range(entry)
            if pkey_range:
                networks.setdefault(network, []).append(pkey_range)
            else:
                networks.setdefault(network, [])
        return networks

    def _parse_network_pkey_range(self, net_pkey_range):
        entry = net_pkey_range.strip()
        msg = None
        if ':' in entry:
            if entry.count(':') != 2:
                msg = (_("Invalid format of pkey value "
                         "range %s ") % net_pkey_range)
            network, pkey_min, pkey_max = entry.split(':')
            if not network:
                msg = (_("Tenant network is missing from "
                         "pkey_range %s ") % net_pkey_range)
            try:
                pkey_min = int(pkey_min)
            except ValueError:
                msg = (_("Bad pkey range value %s, it must "
                         "be an integer ") % net_pkey_range)
            try:
                pkey_max = int(pkey_max)
            except ValueError:
                msg = (_("Bad pkey range value, it must "
                         "be an integer ") % net_pkey_range)
            if msg:
                raise exc.InvalidInput(error_message=msg)
            pkey_range = (pkey_min, pkey_max)
            self.verify_pkey_range(pkey_range)
            return network, pkey_range
        else:
            return entry, None

    def verify_pkey_range(self, pkey_range):
        if pkey_range[0] > pkey_range[1]:
            raise("Invalid Pkey range limit should be less than max")
        # equal to 0x7fff as its reserved.
        for pkey_tag in pkey_range:
            if pkey_tag >= 32767:
                msg = (_("Pkey value is 0x7fff is reserved "))
                raise exc.InvalidInput(error_message=msg)
