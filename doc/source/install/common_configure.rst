2. Edit the ``/etc/networking_netronome/networking_netronome.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://networking_netronome:NETWORKING_NETRONOME_DBPASS@controller/networking_netronome
