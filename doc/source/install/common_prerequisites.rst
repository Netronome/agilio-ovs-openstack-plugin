Prerequisites
-------------

Before you install and configure the Agilio OVS Networking service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p

   * Create the ``networking_netronome`` database:

     .. code-block:: none

        CREATE DATABASE networking_netronome;

   * Grant proper access to the ``networking_netronome`` database:

     .. code-block:: none

        GRANT ALL PRIVILEGES ON networking_netronome.* TO 'networking_netronome'@'localhost' \
          IDENTIFIED BY 'NETWORKING_NETRONOME_DBPASS';
        GRANT ALL PRIVILEGES ON networking_netronome.* TO 'networking_netronome'@'%' \
          IDENTIFIED BY 'NETWORKING_NETRONOME_DBPASS';

     Replace ``NETWORKING_NETRONOME_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: none

        exit;

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``networking_netronome`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt networking_netronome

   * Add the ``admin`` role to the ``networking_netronome`` user:

     .. code-block:: console

        $ openstack role add --project service --user networking_netronome admin

   * Create the networking_netronome service entities:

     .. code-block:: console

        $ openstack service create --name networking_netronome --description "Agilio OVS Networking" agilio ovs networking

#. Create the Agilio OVS Networking service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        agilio ovs networking public http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        agilio ovs networking internal http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        agilio ovs networking admin http://controller:XXXX/vY/%\(tenant_id\)s
