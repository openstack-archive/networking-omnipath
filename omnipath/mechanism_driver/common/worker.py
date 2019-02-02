# Copyright (c) 2018 Intel Corporation
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


from neutron_lib import worker

from oslo_log import log as logging
from oslo_service import loopingcall


LOG = logging.getLogger(__name__)


class OmnipathWorker(worker.BaseWorker):
    def __init__(self, sync_func, sync_time=None):
        self._sync_func = sync_func
        self._sync_time = 60
        if sync_time:
            self._sync_time = sync_time
        self._loop = None
        super(OmnipathWorker, self).__init__()

    def start(self):
        super(OmnipathWorker, self).start()
        if self._loop is None:
            self._loop = loopingcall.FixedIntervalLoopingCall(self._sync_func)
        LOG.info("Starting omnipath worker")
        self._loop.start(interval=self._sync_time)

    def stop(self):
        if self._loop is not None:
            LOG.info("Stopping omnipath worker")
            self._loop.stop()

    def wait(self):
        if self._loop is not None:
            LOG.info("Waiting omnipath worker")
            self._loop.wait()
        self._loop = None

    def reset(self):
        LOG.info("Reseting omnipath worker")
        self.stop()
        self.wait()
        self.start()
