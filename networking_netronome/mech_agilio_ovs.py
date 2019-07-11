# Copyright (c) 2019 Netronome Systems Pty. Ltd.
# Copyright (c) 2013 OpenStack Foundation
# All Rights Reserved.
#
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

# Derived from
# neutron/plugins/ml2/drivers/openvswitch/mech_driver/mech_openvswitch.py

from neutron.plugins.ml2.drivers.openvswitch.mech_driver.mech_openvswitch \
    import OpenvswitchMechanismDriver
from neutron_lib.api.definitions import portbindings
from neutron_lib.api.definitions.portbindings import VNIC_DIRECT
from neutron_lib.api.definitions.portbindings import VNIC_NORMAL
from neutron_lib.api.definitions.portbindings import VNIC_TYPE
from neutron_lib.api.definitions.portbindings import VNIC_VIRTIO_FORWARDER


class AgilioOvsMechanismDriver(OpenvswitchMechanismDriver):
    """Extend the Openvswitch Mechanism Driver to support Agilio OVS NICs.

    This mechanism driver introduces extended functionality into the
    Openvswitch driver in order to support accelerated SR-IOV and
    vhost-user VNIC types.
    """

    def __init__(self):
        super(AgilioOvsMechanismDriver, self).__init__()
        self.supported_vnic_types += [VNIC_VIRTIO_FORWARDER]
        self.vif_type = 'agilio_ovs'

    def _pre_get_vif_details(self, agent, context):
        vif_details = super(
            AgilioOvsMechanismDriver,
            self)._pre_get_vif_details(agent, context)
        if context.current[VNIC_TYPE] == VNIC_VIRTIO_FORWARDER:
            sock_path = self.agent_vhu_sockpath(agent, context.current['id'])
            mode = portbindings.VHOST_USER_MODE_SERVER
            vif_details[portbindings.VHOST_USER_SOCKET] = sock_path
            vif_details[portbindings.VHOST_USER_MODE] = mode
            vif_details[portbindings.VHOST_USER_OVS_PLUG] = True
            vif_details[portbindings.CAP_PORT_FILTER] = False
            vif_details[portbindings.OVS_HYBRID_PLUG] = False
        return vif_details

    def bind_port(self, context):
        # Call the grandparent method
        super(OpenvswitchMechanismDriver, self).bind_port(context)

    def get_vif_type(self, context, agent, segment):
        vnic_type = context.current.get(VNIC_TYPE, VNIC_NORMAL)
        if (vnic_type == VNIC_DIRECT or vnic_type == VNIC_VIRTIO_FORWARDER):
            return self.vif_type
        return self.get_supported_vif_type(agent)
