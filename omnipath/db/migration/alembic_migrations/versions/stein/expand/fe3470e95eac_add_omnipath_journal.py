# Copyright 2019 OpenStack Foundation
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

"""add_omnipath_journal

Revision ID: fe3470e95eac
Revises: initial_branchpoint
Create Date: 2019-02-05 23:05:47.753557

"""

# revision identifiers, used by Alembic.
revision = 'fe3470e95eac'
down_revision = 'initial_branchpoint'

from alembic import op
from neutron_lib.db import sqlalchemytypes
from oslo_utils import timeutils
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'omnipath_revision_journal',
        sa.Column('standard_attr_id', sa.BigInteger, nullable=True,
                  unique=True),
        sa.Column('resource_uuid', sa.String(36), primary_key=True),
        sa.Column('resource_type', sa.String(36), primary_key=True),
        sa.Column('revision_number', sa.BigInteger, nullable=False,
                  default=-1),
        sa.Column('created_at', sqlalchemytypes.TruncatedDateTime,
                  default=timeutils.utcnow, nullable=False),
        sa.Column('updated_at', sqlalchemytypes.TruncatedDateTime,
                  onupdate=timeutils.utcnow),
        sa.Column('data', sa.PickleType, nullable=True),
        sa.Column('state', sa.Enum('pending', 'failed', 'completed',
                                   'waiting', name='state'),
                  nullable=False, default='pending'),
        sa.ForeignKeyConstraint(
            ['standard_attr_id'], ['standardattributes.id'],
            ondelete='SET NULL')
    )
