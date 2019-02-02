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

from neutron_lib import exceptions

from neutron._i18n import _


class FabricAgentCLIError(paramiko.SSHException):
    """Fabric Agent exception"""
    message = _("Unable to connect Fabric Agent.")


class FabricAgentUnknownCommandError(exceptions.NeutronException):
    """Fabric agent unknown command exception"""
    message = _("fabric agent doesn't recognize the instructed command")


class OmnipathResourceExists(exceptions.InUse):
    """Unable to delete resource """
    message = _("Unable to delete resource %(resource)s. "
                "with id %(res_id)s.")


class FabricAgentBadOperation(exceptions.BadRequest):
    """Agent operation exception"""
    message = ("Bad request resource request failed. ")


class NetworkCreateException(exceptions.NeutronException):
    """Fabric Agent network create exception"""
    message = ("Unable to create network %(net_id). ")
