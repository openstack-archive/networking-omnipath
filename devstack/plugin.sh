#!/bin/bash

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

# devstack/plugin.sh
# networking-ovn actions for devstack plugin framework

# Save trace setting
set +o xtrace
source $TOP_DIR/lib/neutron-legacy
NETWORKING_OMNIPATH_DIR=$DEST/networking-omnipath

source $NETWORKING_OMNIPATH_DIR/devstack/functions

# main loop
if is_service_enabled q-svc || is_service_enabled neutron-api; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
       install_omnipath
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
       install_omnipath
    fi

    if [[ "$1" == "unstack" ]]; then
       remove_omnipath
    fi

   if [[ "$1" == "clean" ]]; then
       remove_omnipath
   fi
fi
