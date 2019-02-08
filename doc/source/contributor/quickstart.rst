.. _quickstart:

=====================
Developer Quick-Start
=====================

This is a quick walkthrough to get you started developing code for
networking-omnipath. This assumes you are already familiar with submitting code
reviews to an OpenStack project.

.. see also::

   https://docs.openstack.org/infra/manual/developers.html

Setup Dev Environment
=====================

Install OS-specific prerequisites::

    # Ubuntu/Debian 14.04:
    sudo apt-get update
    sudo apt-get install python-dev libssl-dev libxml2-dev curl \
                         libmysqlclient-dev libxslt1-dev libpq-dev git \
                         libffi-dev gettext build-essential

    # CentOS/RHEL 7.2:
    sudo yum install python-devel openssl-devel mysql-devel curl \
                     libxml2-devel libxslt-devel postgresql-devel git \
                     libffi-devel gettext gcc

    # openSUSE/SLE 12:
    sudo zypper --non-interactive install git libffi-devel curl \
                        libmysqlclient-devel libopenssl-devel libxml2-devel \
                        libxslt-devel postgresql-devel python-devel \
                        gettext-runtime

Install pip::

    curl -s https://bootstrap.pypa.io/get-pip.py | sudo python

Install common prerequisites::

    sudo pip install virtualenv flake8 tox testrepository git-review

You may need to explicitly upgrade virtualenv if you've installed the one
from your OS distribution and it is too old (tox will complain). You can
upgrade it individually, if you need to::

    sudo pip install -U virtualenv

Networking-omnipath source code should be pulled directly from git::

    # TODO(manjeets) update urls once accepted to openstack namespace
    # from your home or source directory
    cd ~
    git clone https://git.intel.com/manjeets/networking-omnipath
    cd networking-omnipath


For installation of networking-omnipath refer to :doc:`/install/index`.
For testing refer to :doc:`Testing <testing>` guide.
