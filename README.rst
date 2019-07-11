===============================
agilio-ovs-openstack-plugin
===============================

Neutron ML2 and OS-VIF plugin for Agilio OVS

This provides the custom ML2 mechanism driver and OS-VIF plugins required to
support Netronome Agilio OVS hardware in OpenStack. This plugin is currently
in pre-release and is intended to aid in integration testing with core
OpenStack.

Note: this plugin requires a recent version of upstream OpenStack.
See: https://blueprints.launchpad.net/nova/+spec/netronome-smartnic-enablement
This code is fully functional, documentation and unit tests are in development.
Source: https://github.com/Netronome/agilio-ovs-openstack-plugin

devstack demo playbook
----------------------

This section describes how to use the demo playbook in the ``ansible/``
directory of this repository.

Requirements:
    * You will need a node that functions as an Ansible executor. For example,
      you might need to execute the following on CentOS 7.x::

        sudo yum -y install centos-release-ansible26.noarch
        sudo yum -y install ansible python2-jmespath git vim

    * A target node, with CentOS 7 installed, with a Netronome Agilio OVS
      compatible NIC.

Quickstart guide:
    * Clone the repo into a temporary directory on the Ansible executor::

        git clone https://github.com/Netronome/agilio-ovs-openstack-plugin.git

    * Change to the ``ansible`` directory and modify ``hosts.yaml`` and
      ``playbook.yaml`` with the correct settings::

        cd agilio-ovs-openstack-plugin
        vim hosts.yaml
        vim playbook.yaml

    * Run the ``prepare-devstack.sh`` script::

        ./prepare-devstack.sh

    * Shell into the host and reboot it::

        ssh centos@example.com
        # Verify environment
        sudo reboot

    * Shell into the host and run devstack::

        ssh stack@example.com
        # Note, the playbook creates a ``stack`` user!
        cd devstack
        ./stack.sh
