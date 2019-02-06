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


from neutron.objects import base
from neutron.objects import common_types
from oslo_versionedobjects import fields as obj_fields

from omnipath.db import models as omni_model


# TODO(manjeets) move this custom range type
# to objects/common_types
class PkeyRange(common_types.RangeConstrainedInteger):
    def __init__(self, **kwargs):
        super(PkeyRange, self).__init__(start=0,
                                        end=32766,
                                        **kwargs)


class PkeyRangeField(obj_fields.AutoTypedField):
    AUTO_TYPE = PkeyRange()


@base.NeutronObjectRegistry.register
class OmniPathAllocation(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = omni_model.OmniPathAllocation

    fields = {
        'physical_network': obj_fields.StringField(),
        'pkey': PkeyRangeField(),
        'allocated': obj_fields.BooleanField(),
    }

    primary_keys = ['physical_network', 'pkey']
