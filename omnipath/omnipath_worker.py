# Copyright (c) 2017 Red Hat, Inc.
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

import atexit
import os

from neutron_lib import worker
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import loopingcall

from neutron._i18n import _
from neutron.agent.linux import daemon

from omnipath import omnipath_thread as journal

LOG = logging.getLogger(__name__)


class OmniPathPeriodicProcessor(worker.BaseWorker):
    """Responsible for running the periodic processing of the journal.

    This is a separate worker as the regular journal thread is called when an
    operation finishes and that run will take care of any and all entries
    that might be present in the journal, including the one relating to that
    operation.

    A periodic run over the journal is thus necessary for cases when journal
    entries in the aforementioned run didn't process correctly due to some
    error (usually a connection problem) and need to be retried.
    """
    def __init__(self):
        super(OmniPathPeriodicProcessor, self).__init__()
        self._journal = journal.OmniPathThread(start_thread=False)
        self._interval = 20
        self._timer = None
        self._running = None
        self.pidfile = None

    def _create_pidfile(self):
        pidfile = os.path.join(cfg.CONF.state_path,
                               type(self).__name__.lower() + '.pid')
        self.pidfile = daemon.Pidfile(pidfile, 'python')

        if self._running is None:
            atexit.register(self._delete_pidfile)

        self.pidfile.write(os.getpid())

    def _delete_pidfile(self):
        if self.pidfile is not None:
            self.pidfile.unlock()
            os.remove(str(self.pidfile))
            self.pidfile = None

    def start(self):
        if self._running:
            raise RuntimeError(
                _("Thread has to be stopped before started again")
            )

        super(OmniPathPeriodicProcessor, self).start()
        LOG.debug('OmniPathPeriodicProcessor starting')
        self._journal.start()
        self._timer = loopingcall.FixedIntervalLoopingCall(self._call_journal)
        self._timer.start(self._interval)
        self._create_pidfile()
        self._running = True

    def stop(self):
        if not self._running:
            return
        LOG.debug('OmniPathPeriodicProcessor stopping')
        self._journal.stop()
        self._timer.stop()
        self._delete_pidfile()
        super(OmniPathPeriodicProcessor, self).stop()
        self._running = False

    def wait(self):
        pass

    def reset(self):
        pass

    def _call_journal(self):
        pass

    def _start_maintenance_task(self):
        pass
