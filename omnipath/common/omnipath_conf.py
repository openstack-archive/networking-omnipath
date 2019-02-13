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


from oslo_config import cfg
from oslo_log import log as logging

from neutron._i18n import _

LOG = logging.getLogger(__name__)

opt_group = cfg.OptGroup(name="ml2_omnipath",
                         title="Omnipath configuration")

omnipath_opts = [
    cfg.StrOpt(
        "ip_address",
        default="localhost",
        help=_("Host IP Address of the OPA FM Agent")),
    cfg.StrOpt(
        "username",
        help=_("Username of the OPA FM Agent")),
    cfg.StrOpt(
        "ssh_key",
        help=_("Private key path to access OPA FM Agent")),
    cfg.StrOpt(
        "poll_interval",
        help=_("Interval in seconds which a full sync is done"
               "with OPA FM Agent ")),
]


cfg.CONF.register_opts(omnipath_opts, "ml2_omnipath")


def list_opts():
    return [('ml2_omnipath', omnipath_opts)]
