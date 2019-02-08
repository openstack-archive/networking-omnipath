OMNIPATH Driver Architecture
============================

This document covers architectural concepts of the omnipath mechanism
driver. Although 'driver' is an ML2 term, it's used widely in to refer
to any implementation of APIs. Any mention of ML2 in this document is
solely for reference purposes.

Mechanism Driver OmniPath
-------------------------

The mechanism driver gets the requests from neutron api for network
create, delete and port create, delete and then logs them into a
revision_journal table and then there's post commit methods for each
operation that wakes the worker thread to prepare the request and
dispatch it to OPA binary over SSH.

The revision journal entry is recorded in the pre-commit phase of each
operation and then postcommit phase wake the working thread to post the
requests one by one to switch fabric. The port binding requests will be
batched in a way that all the port binding requests for same network or
virtual fabric are sent in one request.

# TODO(manjeets) add architecture figure.

