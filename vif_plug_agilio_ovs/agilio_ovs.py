# Derived from os-vif/vif_plug_ovs/ovs.py
#
# Copyright (C) 2017 Netronome Systems, Inc.
# Copyright (C) 2011 Midokura KK
# Copyright (C) 2011 Nicira, Inc
# Copyright 2011 OpenStack Foundation
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

from os_vif import objects as obj
from os_vif.objects.vif import VIFPortProfileOpenVSwitch

from vif_plug_agilio_ovs import agilio_linux_net

from vif_plug_ovs import exception
from vif_plug_ovs import linux_net
from vif_plug_ovs import ovs


class AgilioOvsPlugin(ovs.OvsPlugin):
    """An OS-VIF plugin that extends the OVS plugin with Agilio support.

    """

    def describe(self):
        pp_ovs = obj.host_info.HostPortProfileInfo(
            profile_object_name=obj.vif.VIFPortProfileOpenVSwitch.__name__,
            min_version="1.0",
            max_version="1.0",
        )
        pp_ovs_representor = obj.host_info.HostPortProfileInfo(
            profile_object_name=obj.vif.VIFPortProfileOVSRepresentor.__name__,
            min_version="1.0",
            max_version="1.0",
        )
        return obj.host_info.HostPluginInfo(
            plugin_name='agilio_ovs',
            vif_info=[
                obj.host_info.HostVIFInfo(
                    vif_object_name=obj.vif.VIFBridge.__name__,
                    min_version="1.0",
                    max_version="1.0",
                    supported_port_profiles=[pp_ovs]),
                obj.host_info.HostVIFInfo(
                    vif_object_name=obj.vif.VIFOpenVSwitch.__name__,
                    min_version="1.0",
                    max_version="1.0",
                    supported_port_profiles=[pp_ovs]),
                obj.host_info.HostVIFInfo(
                    vif_object_name=obj.vif.VIFVHostUser.__name__,
                    min_version="1.0",
                    max_version="1.0",
                    supported_port_profiles=[pp_ovs, pp_ovs_representor]),
                obj.host_info.HostVIFInfo(
                    vif_object_name=obj.vif.VIFHostDevice.__name__,
                    min_version="1.0",
                    max_version="1.0",
                    supported_port_profiles=[pp_ovs, pp_ovs_representor]),
            ])

    def _get_representor(self, vif):
        if isinstance(vif, obj.vif.VIFHostDevice):
            pci_addr = vif.dev_address
        elif 'datapath_offload' in vif.port_profile \
             and hasattr(vif.port_profile, 'datapath_offload') \
             and isinstance(vif.port_profile.datapath_offload,
                            obj.vif.DatapathOffloadRepresentor):
            pci_addr = vif.port_profile.datapath_offload.representor_address
        elif 'representor_address' in vif.port_profile \
             and hasattr(vif.port_profile, 'representor_address'):
            pci_addr = vif.port_profile.representor_address
        else:
            # TODO(jangutter): New exception is needed
            raise exception.WrongPortProfile(
                profile=vif.port_profile.__class__.__name__)
        vf_num = linux_net.get_vf_num_by_pci_address(pci_addr)
        pf_ifname = linux_net.get_ifname_by_pci_address(
            pci_addr, pf_interface=True, switchdev=True)
        representor = linux_net.get_representor_port(pf_ifname, vf_num)

        return {
            'address': pci_addr,
            'name': representor,
            'pfname': pf_ifname,
            'vfno': vf_num
        }

    def _plug_representor(self, vif, instance_info, representor):
        datapath = self._get_vif_datapath_type(vif)
        self.ovsdb.ensure_ovs_bridge(vif.network.bridge, datapath)
        linux_net.set_interface_state(representor['name'], 'up')
        self._create_vif_port(vif, representor['name'], instance_info)

    def _unplug_representor(self, vif, representor):
        self.ovsdb.delete_ovs_vif_port(
            vif.network.bridge, representor['name'], delete_netdev=False)
        linux_net.set_interface_state(representor['name'], 'down')

    def _plug_forwarder(self, vif, representor):
        agilio_linux_net.bind_driver(representor['address'], 'vfio-pci')
        # TODO(jangutter): set vf MAC to vif.address
        agilio_linux_net.plug_forwarder(representor['address'], vif.path)

    def _unplug_forwarder(self, vif, representor):
        agilio_linux_net.unplug_forwarder(representor['address'], vif.path)

    def plug(self, vif, instance_info):
        if not hasattr(vif, "port_profile"):
            raise exception.MissingPortProfile()
        if not isinstance(vif.port_profile, VIFPortProfileOpenVSwitch):
            raise exception.WrongPortProfile(
                profile=vif.port_profile.__class__.__name__)
        representor = self._get_representor(vif)
        if isinstance(vif, obj.vif.VIFHostDevice):
            self._plug_representor(vif, instance_info, representor)
        elif isinstance(vif, obj.vif.VIFVHostUser):
            self._plug_representor(vif, instance_info, representor)
            self._plug_forwarder(vif, representor)

    def unplug(self, vif, instance_info):
        if not hasattr(vif, "port_profile"):
            raise exception.MissingPortProfile()
        if not isinstance(vif.port_profile, VIFPortProfileOpenVSwitch):
            raise exception.WrongPortProfile(
                profile=vif.port_profile.__class__.__name__)
        representor = self._get_representor(vif)
        if isinstance(vif, obj.vif.VIFHostDevice):
            self._unplug_representor(vif, representor)
        elif isinstance(vif, obj.vif.VIFVHostUser):
            self._unplug_representor(vif, representor)
            self._unplug_forwarder(vif, representor)
