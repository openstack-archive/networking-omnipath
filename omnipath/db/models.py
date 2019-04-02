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

from neutron_lib.db import model_base
from neutron_lib.db import sqlalchemytypes
from oslo_utils import timeutils
import sqlalchemy as sa


class OmniPathRevisionNumbers(model_base.BASEV2):
    __tablename__ = 'omnipath_revision_journal'
    __table_args__ = (
        model_base.BASEV2.__table_args__
    )
    standard_attr_id = sa.Column(
        sa.BigInteger().with_variant(sa.Integer(), 'sqlite'),
        sa.ForeignKey('standardattributes.id', ondelete='SET NULL'),
        unique=True)
    resource_uuid = sa.Column(sa.String(36), nullable=False, primary_key=True)
    resource_type = sa.Column(sa.String(36), nullable=False, primary_key=True)
    revision_number = sa.Column(
        sa.BigInteger().with_variant(sa.Integer(), 'sqlite'),
        default=0, nullable=False)
    data = sa.Column(sa.PickleType, nullable=True)
    created_at = sa.Column(sqlalchemytypes.TruncatedDateTime,
                           default=timeutils.utcnow, nullable=False)
    updated_at = sa.Column(sqlalchemytypes.TruncatedDateTime,
                           onupdate=timeutils.utcnow)
    state = sa.Column(sa.Enum('pending', 'failed', 'completed',
                              'waiting'),
                      nullable=False, default='pending')
