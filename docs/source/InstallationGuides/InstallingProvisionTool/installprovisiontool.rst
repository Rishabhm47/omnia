Provisioning the cluster
--------------------------

1. Edit the ``input/provision_config.yml`` file to update the required variables.

.. warning:: The IP address *192.168.25.x* is used for PowerVault Storage communications. Therefore, do not use this IP address for other configurations.

2. To deploy the Omnia provision tool, run the following command ::

    cd provision
    ansible-playbook provision.yml

3. By running ``provision.yml``, the following configurations take place:

a. All compute nodes in cluster will be enabled for PXE boot with osimage mentioned in ``provision_config.yml``.

b. A PostgreSQL database is set up with all relevant cluster information such as MAC IDs, hostname, admin IP, infiniband IPs, BMC IPs etc.

    To access the DB, run: ::

            psql -U postgres

            \c omniadb


    To view the schema being used in the cluster: ``\dn``

    To view the tables in the database: ``\dt``

    To view the contents of the ``nodeinfo`` table: ``select * from cluster.nodeinfo;`` ::


                    id | serial  |   node    |       hostname        | admin_mac |  admin_ip   |   bmc_ip    | ib_ip | status | bmc_mode
                    ----+---------+-----------+-----------------------+-----------+-------------+-------------+-------+--------+----------
                      1 | 4FC45X2 | node00001 | node00001.spring.test |           | 172.17.0.25 | 172.29.0.25 | 172.35.0.25 |        | static
                      2 | FBB65X2 | node00002 | node00002.spring.test |           | 172.17.0.35 | 172.29.0.35 | 172.35.0.35 |        | static


Possible values of status are static, powering-on, installing, booting, post-booting, booted, failed. The status will be updated every 3 minutes.

c. Offline repositories will be created based on the OS being deployed across the cluster.

d. The xCAT post bootscript is configured to assign the hostname (with domain name) on the provisioned servers.

Once the playbook execution is complete, ensure that PXE boot and RAID configurations are set up on remote nodes. Users are then expected to reboot target servers discovered via SNMP or mapping to provision the OS.

.. note::

    * If the cluster does not have access to the internet, AppStream will not function.  To provide internet access through the control plane (via the PXE network NIC), update ``primary_dns`` and ``secondary_dns`` in ``provision_config.yml`` and run ``provision.yml``

    * All ports required for xCAT to run will be opened (For a complete list, check out the `Security Configuration Document <../../SecurityConfigGuide/ProductSubsystemSecurity.html#firewall-settings>`_).

    * After running ``provision.yml``, the file ``input/provision_config.yml`` will be encrypted. To edit the file, use the command: ``ansible-vault edit provision_config.yml --vault-password-file .provision_vault_key``

    * To re-provision target servers ``provision.yml`` can be re-run. Alternatively, use the following steps (as an example, we will be re-provisioning rhels8.6.0-x86_64-install-compute):

         * Use ``lsdef -t osimage | grep install-compute`` to get a list of all valid OS profiles.

         * Use ``nodeset all osimage=rhels8.6.0-x86_64-install-compute`` to provision the OS on the target server.

         * PXE boot the target server to bring up the OS.

    * Post execution of ``provision.yml``, IPs/hostnames cannot be re-assigned by changing the mapping file. However, the addition of new nodes is supported as explained below.

.. warning:: Once xCAT is installed, restart your SSH session to the control plane to ensure that the newly set up environment variables come into effect.


Installing CUDA
++++++++++++++++

**Using the provision tool**

* If ``cuda_toolkit_path`` is provided  in ``input/provision_config.yml`` and NVIDIA GPUs are available on the target nodes, CUDA packages will be deployed post provisioning without user intervention.

**Using the Accelerator playbook**

* CUDA can also be installed using `accelerator.yml <../../Roles/Accelerator/index.html>`_ after provisioning the servers (Assuming the provision tool did not install CUDA packages).

.. note:: The CUDA package can be downloaded from `here <https://developer.nvidia.com/cuda-downloads>`_

Installing OFED
+++++++++++++++++

**Using the provision tool**

* If ``mlnx_ofed_path`` is provided  in ``input/provision_config.yml`` and Mellanox NICs are available on the target nodes, OFED packages will be deployed post provisioning without user intervention.

**Using the Network playbook**

* OFED can also be installed using `network.yml <../../Roles/Network/index.html>`_ after provisioning the servers (Assuming the provision tool did not install OFED packages).

.. note:: The OFED package can be downloaded from `here <https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/>`_ .

Assigning infiniband IPs
+++++++++++++++++++++++++++

When ``ib_nic_subnet`` is provided in ``input/provision_config.yml``, the infiniband NIC on target nodes are assigned IPv4 addresses within the subnet without user intervention. When PXE range and Infiniband subnet are provided, the infiniband NICs will be assigned IPs with the same 3rd and 4th octets as the PXE NIC.

* For example on a target node, when the PXE NIC is assigned 10.17.0.101, and the Infiniband NIC is assigned 10.29.0.101 (where ``ib_nic_subnet`` is 10.29.0.0).

.. note::  The IP is assigned to the interface **ib0** on target nodes only if the interface is present in **active** mode. If no such NIC interface is found, xCAT will list the status of the node object as failed.

Assigning BMC IPs
++++++++++++++++++

When target nodes are discovered via SNMP or mapping files (ie ``discovery_mechanism`` is set to snmp or mapping in ``input/provision_config.yml``), the ``bmc_nic_subnet`` in ``input/provision_config.yml`` can be used to assign BMC IPs to iDRAC without user intervention. When PXE range and BMC subnet are provided, the iDRAC NICs will be assigned IPs with the same 3rd and 4th octets as the PXE NIC.

* For example on a target node, when the PXE NIC is assigned 10.17.0.101, and the iDRAC NIC is assigned 10.27.0.101 (where ``bmc_nic_subnet`` is 10.27.0.0).

Using multiple versions of a given OS
+++++++++++++++++++++++++++++++++++++++

Omnia now supports deploying different versions of the same OS. With each run of ``provision.yml``, a new deployable OS image is created with a distinct type (rocky or RHEL) and version (8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7) depending on the values provided in ``input/provision_config.yml``.

.. note:: While Omnia deploys the minimal version of the OS, the multiple version feature requires that the Rocky full (DVD) version of the OS be provided.

DHCP routing for internet access
++++++++++++++++++++++++++++++++

Omnia now supports DHCP routing via the control plane. To enable routing, update the ``primary_dns`` and ``secondary_dns`` in ``input/provision_config.yml`` with the appropriate IPs (hostnames are currently not supported). For compute nodes that are not directly connected to the internet (ie only PXE network is configured), this configuration allows for internet connectivity.

Disk partitioning
++++++++++++++++++

Omnia now allows for customization of disk partitions applied to remote servers. The disk partition ``desired_capacity`` has to be provided in MB. Valid ``mount_point`` values accepted for disk partition are ``/home``, ``/var``, ``/tmp``, ``/usr``, ``swap``. Default partition size provided for ``/boot`` is 1024MB, ``/boot/efi`` is 256MB and the remaining space to ``/`` partition.  Values are accepted in the form of JSON list such as:

::

    disk_partition:
        - { mount_point: "/home", desired_capacity: "102400" }
        - { mount_point: "swap", desired_capacity: "10240" }
