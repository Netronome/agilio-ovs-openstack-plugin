# Derived from os-vif/vif_plug_ovs/tests/unit/test_plugin.py
#
# Copyright (c) 2017 Netronome Systems Pty. Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock
import testtools

from os_vif import objects
from os_vif.objects import fields

from vif_plug_agilio_ovs import agilio_linux_net
from vif_plug_agilio_ovs import agilio_ovs


class PluginTest(testtools.TestCase):

    def __init__(self, *args, **kwargs):
        super(PluginTest, self).__init__(*args, **kwargs)

        objects.register_all()

        self.subnet_bridge_4 = objects.subnet.Subnet(
            cidr='101.168.1.0/24',
            dns=['8.8.8.8'],
            gateway='101.168.1.1',
            dhcp_server='191.168.1.1')

        self.subnet_bridge_6 = objects.subnet.Subnet(
            cidr='101:1db9::/64',
            gateway='101:1db9::1')

        self.subnets = objects.subnet.SubnetList(
            objects=[self.subnet_bridge_4,
                     self.subnet_bridge_6])

        self.network_ovs = objects.network.Network(
            id='437c6db5-4e6f-4b43-b64b-ed6a11ee5ba7',
            bridge='br0',
            subnets=self.subnets,
            vlan=99)

        self.profile_ovs = objects.vif.VIFPortProfileOVSRepresentor(
            interface_id='e65867e0-9340-4a7f-a256-09af6eb7a3aa',
            representor_name='repr_name',
            representor_address='0002:24:12.3')

        self.vif_virtioforwarder = objects.vif.VIFVHostUser(
            id='b679325f-ca89-4ee0-a8be-6db1409b69ea',
            address='ca:fe:de:ad:be:ef',
            network=self.network_ovs,
            path='/var/run/openvswitch/vhub679325f-ca',
            mode='client',
            port_profile=self.profile_ovs)

        self.vif_passthrough = objects.vif.VIFHostDevice(
            id='b679325f-ca89-4ee0-a8be-6db1409b69ea',
            address='ca:fe:de:ad:be:ef',
            network=self.network_ovs,
            dev_type=fields.VIFHostDeviceDevType.ETHERNET,
            dev_address='0002:24:12.3',
            bridge_name='br-int',
            port_profile=self.profile_ovs)

        self.instance = objects.instance_info.InstanceInfo(
            name='demo',
            uuid='f0000000-0000-0000-0000-000000000001')

    @mock.patch.object(agilio_linux_net, 'create_ovs_vif_port')
    def test_create_vif_port(self, mock_create_ovs_vif_port):
        plugin = agilio_ovs.AgilioOvsPlugin.load('agilio_ovs')
        plugin._create_vif_port(
            self.vif_virtioforwarder, mock.sentinel.vif_name, self.instance)
        mock_create_ovs_vif_port.assert_called_once_with(
            self.vif_virtioforwarder.network.bridge, mock.sentinel.vif_name,
            self.vif_virtioforwarder.port_profile.interface_id,
            self.vif_virtioforwarder.address, self.instance.uuid,
            plugin.config.network_device_mtu,
            timeout=plugin.config.ovs_vsctl_timeout)
