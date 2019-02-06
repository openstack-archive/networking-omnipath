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


from omnipath.db import models


def record_pending_entry(context, res_uuid,
                         res_type, data,
                         state='pending'):
    row = models.OmniPathRevisionNumbers(
        resource_uuid=res_uuid,
        resource_type=res_type,
        data=data,
        state=state)
    context.session.add(row)


def get_resource_row(context, res_uuid, res_type):
    res = context.session.query(models.OmniPathRevisionNumbers).filter_by(
        resource_uuid=res_uuid, resource_type=res_type).first()
    return res


def get_all_entries_by_state(context, state):
    all_entries = context.session.query(
        models.OmniPathRevisionNumbers).filter_by(
            state=state)
    return all_entries.all()


def update_row_state(context, state, row):
    row.state = state
    context.session.merge(row)


def update_multiple_rows(context, state, res_ids):
    all_entries = context.session.query(
        models.OmniPathRevisionNumbers).filter(
            models.OmniPathRevisionNumbers.resource_uuid.in_(
                res_ids))
    for row in all_entries.all():
        update_row_state(context, state, row)


def mark_entry_complete(context, row, status):
    if row:
        row.update(status='complete')
