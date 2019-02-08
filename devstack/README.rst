======================
 Enabling in Devstack
======================

1. Clone networking-omnipath and devstack::

    git clone https://github.intel.com/manjeets/networking-omnipath
    git clone https://github.com/openstack-dev/devstack

2. Copy the sample local.conf over::

     cp networking-omnipath/devstack/local_ironic.conf.example devstack/local.conf

3. Add HOST_IP value in local.conf and enable networking-omnipath plugin:

   Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin networking-omnipath /opt/stack/networking-omnipath


4.  To enable OmniPath Backend add these parameters in the local.conf::

     > cat local.conf
     [ml2_omnipath]
     username="root"
     ssh_key="<path to public ssh key authorized to access fabric>"
     ip_address="<ip address of fabric>"
     pkey_ranges="pkey:1:2000"

5. run ``stack.sh``

