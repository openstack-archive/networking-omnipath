.. _installation:

Installation
============

The ``networking-omnipath`` repository includes integration with DevStack that
enables creation of a simple development and test environment for openstack
neutron with OmniPath fabric.

* Controller - Runs OpenStack control plane services such as REST APIs
  and databases.

* Network - Provides connectivity between provider (public) and project
  (private) networks. L3 functionality is optional when using it for
  baremetal provisioning with OmniPath Fabric.

* Compute - Runs the hypervisor and optional layer-2 agent, if omnipath switching
  is used along with other L2 backends then a layer-2 agent may be needed on compute.


Networking-omnipath Installation
---------------------------

.. code-block:: console

   # git clone https://github.intel.com/manjeets/networking-omnipath
   # cd networking-omnipath
   # sudo python setup.py install

.. note::

   pip will be used later on when package becomes open source


Networking-omnipath Configuration
----------------------------------

All related neutron services need to be restarted after configuration change.

#. Configure Openstack neutron server to enable networking-omnipath as an
   ML2 driver. Edit the ``/etc/neutron/neutron.conf`` file:

   * Enable the ML2 core plug-in.

     .. code-block:: ini

        [DEFAULT]
        ...
        core_plugin = neutron.plugins.ml2.plugin.Ml2Plugin

   * (Optional) L3 plugin is optional but not need and out of scope for this setup.


#. Configure the ML2 plug-in. Edit the
   ``/etc/neutron/plugins/ml2/ml2_conf.ini`` file:

   * Configure the omnipath mechanism driver.

     .. code-block:: ini

        [ml2]
        ...
        mechanism_drivers = omnipath_mech
        type_drivers = local,flat,vlan,vxlan
        tenant_network_types = vlan

	[ml2_type_flat]
        flat_networks = public,PYHSICAL_NET

     .. note::

        The networking-omnipath will use vlan type driver by default.

   * Configure the vlan range.

     .. code-block:: ini

        [ml2_type_vlan]
        ...
        network_vlan_ranges = PHYSICAL_NET:1:1000

     .. note::

	PHYSICAL_NET is the value used for physical network in flat networks.

   * Configure ML2 Omnipath

     .. code-block:: ini

        [ml2_omnipath]

        ...
        username = <OMNIPATH_USERNAME>
        ssh_key = <PATH_TO_SSH_PUBLICKEY>
        ip_address = <IPV4 IP of OPA Binary>
        pkey_ranges = "pkey:1:2000"
