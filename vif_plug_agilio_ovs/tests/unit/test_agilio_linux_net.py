# Derived from os-vif/vif_plug_ovs/tests/unit/test_linux_net.py
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

from oslo_concurrency import processutils

from vif_plug_agilio_ovs import agilio_linux_net
from vif_plug_agilio_ovs import privsep


class LinuxNetTest(testtools.TestCase):

    def setUp(self):
        super(LinuxNetTest, self).setUp()

        privsep.vif_plug.set_client_mode(False)

    def test_ovs_vif_port_cmd(self):
        expected = ['--', 'add-port',
                    'fake-bridge', 'fake-dev',
                    '--', 'set', 'Interface', 'fake-dev',
                    'external-ids:iface-id=fake-iface-id',
                    'external-ids:iface-status=active',
                    'external-ids:attached-mac=fake-mac',
                    'external-ids:vm-uuid=fake-instance-uuid']
        cmd = agilio_linux_net._create_ovs_vif_cmd(
            'fake-bridge', 'fake-dev', 'fake-iface-id', 'fake-mac',
            'fake-instance-uuid')

        self.assertEqual(expected, cmd)

        expected += ['type=fake-type']
        cmd = agilio_linux_net._create_ovs_vif_cmd(
            'fake-bridge', 'fake-dev', 'fake-iface-id', 'fake-mac',
            'fake-instance-uuid', 'fake-type')
        self.assertEqual(expected, cmd)

        expected += ['options:vhost-server-path=/fake/path']
        cmd = agilio_linux_net._create_ovs_vif_cmd(
            'fake-bridge', 'fake-dev', 'fake-iface-id', 'fake-mac',
            'fake-instance-uuid', 'fake-type', vhost_server_path='/fake/path')
        self.assertEqual(expected, cmd)

    @mock.patch.object(agilio_linux_net, '_create_ovs_bridge_cmd')
    @mock.patch.object(agilio_linux_net, '_ovs_vsctl')
    def test_ensure_ovs_bridge(self, mock_vsctl, mock_create_ovs_bridge):
        bridge = 'fake-bridge'
        dp_type = 'fake-type'
        agilio_linux_net.ensure_ovs_bridge(bridge, dp_type)
        mock_create_ovs_bridge.assert_called_once_with(bridge, dp_type)
        self.assertTrue(mock_vsctl.called)

    def test_create_ovs_bridge_cmd(self):
        bridge = 'fake-bridge'
        dp_type = 'fake-type'
        expected = ['--', '--may-exist', 'add-br', bridge,
                    '--', 'set', 'Bridge', bridge,
                    'datapath_type=%s' % dp_type]
        actual = agilio_linux_net._create_ovs_bridge_cmd(bridge, dp_type)
        self.assertEqual(expected, actual)

    @mock.patch.object(agilio_linux_net, '_ovs_vsctl')
    def test_create_ovs_vif_port(self, mock_vsctl):
        agilio_linux_net.create_ovs_vif_port(
            'fake-bridge', 'fake-dev', 'fake-iface-id', 'fake-mac',
            "fake-instance-uuid", timeout=42)
        mock_vsctl.assert_has_calls([
            mock.call(['--', '--if-exists', 'del-port', 'fake-bridge',
                       'fake-dev'],
                      timeout=42),
            mock.call(['--', 'add-port', 'fake-bridge', 'fake-dev',
                       '--', 'set', 'Interface', 'fake-dev',
                       'external-ids:iface-id=fake-iface-id',
                       'external-ids:iface-status=active',
                       'external-ids:attached-mac=fake-mac',
                       'external-ids:vm-uuid=fake-instance-uuid'],
                      timeout=42)])

    @mock.patch.object(agilio_linux_net, '_ovs_vsctl')
    def test_create_ovs_vif_port_virtioforwarder(self, mock_vsctl):
        agilio_linux_net.create_ovs_vif_port(
            'fake-bridge', 'fake-dev', 'fake-iface-id', 'fake-mac',
            "fake-instance-uuid", virtio_forwarder=42, timeout=None)
        mock_vsctl.assert_has_calls([
            mock.call(['--', '--if-exists', 'del-port', 'fake-bridge',
                       'fake-dev'],
                      timeout=None),
            mock.call(['--', 'add-port', 'fake-bridge', 'fake-dev',
                       '--', 'set', 'Interface', 'fake-dev',
                       'external-ids:iface-id=fake-iface-id',
                       'external-ids:iface-status=active',
                       'external-ids:attached-mac=fake-mac',
                       'external-ids:vm-uuid=fake-instance-uuid',
                       'external-ids:virtio_forwarder=42'],
                      timeout=None)])

    @mock.patch.object(processutils, "execute")
    def test_ovs_vsctl(self, mock_execute):
        args = ['fake-args', 42]
        timeout = 42
        agilio_linux_net._ovs_vsctl(args)
        agilio_linux_net._ovs_vsctl(args, timeout=timeout)
        mock_execute.assert_has_calls([
            mock.call('ovs-vsctl', *args),
            mock.call('ovs-vsctl', '--timeout=%s' % timeout, *args)])

    @mock.patch.object(agilio_linux_net, '_ovs_vsctl')
    def test_delete_ovs_vif_port(self, mock_vsctl):
        bridge = 'fake-bridge'
        dev = 'fake-dev'
        timeout = 120
        agilio_linux_net.delete_ovs_vif_port(bridge, dev, timeout=timeout)
        args = ['--', '--if-exists', 'del-port', bridge, dev]
        mock_vsctl.assert_called_with(args, timeout=timeout)
