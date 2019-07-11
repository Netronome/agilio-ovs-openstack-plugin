# Derived from os-vif/vif_plug_ovs/linux_net.py
#
# Copyright (C) 2017 Netronome Systems, Inc.
# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Linux utilities necessary for Agilio OVS network setup."""


import os

from oslo_concurrency import processutils

from oslo_log import log as logging

from vif_plug_agilio_ovs import privsep

from vif_plug_ovs import exception


LOG = logging.getLogger(__name__)


def _forwarder_port_control(oper, pci_addr, vhu_path):
    cmd = [
        '/usr/lib64/virtio-forwarder/virtioforwarder_port_control.py',
        '%s_sock' % oper,
        '--pci-addr=%s' % pci_addr,
        '--vhost-path=%s' % vhu_path]
    try:
        return processutils.execute(
            *cmd,
            check_exit_code=[0, 1])
    except Exception as e:
        LOG.error("Unable to execute %(cmd)s. Exception: %(exception)s",
                  {'cmd': cmd, 'exception': e})
        raise exception.AgentError(method=cmd)


@privsep.vif_plug.entrypoint
def plug_forwarder(pci_addr, vhu_path):
    _forwarder_port_control('add', pci_addr, vhu_path)


@privsep.vif_plug.entrypoint
def unplug_forwarder(pci_addr, vhu_path):
    _forwarder_port_control('remove', pci_addr, vhu_path)


def _get_sysfs_entry(pci_addr, entry):
    sysfspath = '/sys/bus/pci/devices/%s/%s' % (pci_addr, entry)
    with open(sysfspath, 'r') as sysfsfile:
        return sysfsfile.read()


def _get_driver(pci_addr):
    sysfspath = '/sys/bus/pci/devices/%s/driver' % pci_addr
    try:
        driver = os.path.basename(os.readlink(sysfspath))
    except OSError:
        driver = ''
    return driver


def _unbind_from_driver(pci_addr, driver):
    if _get_driver(pci_addr) == '':
        return

    unbind_path = '/sys/bus/pci/drivers/%s/unbind' % driver
    with open(unbind_path, 'a') as unbind:
        unbind.write(pci_addr)


@privsep.vif_plug.entrypoint
def bind_driver(pci_addr, driver):
    current_driver = _get_driver(pci_addr)
    if current_driver == driver:
        return
    _unbind_from_driver(pci_addr, current_driver)

    # NOTE(jangutter): driver_override is a new race-free way to bind a
    # driver to a specific device, for more info see:
    # https://github.com/torvalds/linux/commit/782a985d7af26db39e86070d28f987c
    override_path = '/sys/bus/pci/devices/%s/driver_override' % pci_addr

    if os.path.exists(override_path):
        with open(override_path, 'w') as driver_override:
            driver_override.write('%s' % driver)
    else:
        # Fall back to classic method: the drawback is that other devices
        # might spontaneously rebind. It's generally not a big issue but
        # sometimes unexpected.
        vendor = int(_get_sysfs_entry(pci_addr, 'vendor'), 0)
        device = int(_get_sysfs_entry(pci_addr, 'device'), 0)
        new_id_path = '/sys/bus/pci/drivers/%s/new_id' % driver
        with open(new_id_path, 'w') as new_id:
            new_id.write('%04x %04x' % (vendor, device))

    # Instead of drivers_probe, just poke the specific driver with the device
    bind_path = '/sys/bus/pci/drivers/%s/bind' % driver
    try:
        with open(bind_path, 'a') as bind:
            bind.write(pci_addr)
    except IOError:
        if _get_driver(pci_addr) == driver:
            pass
        else:
            raise

    if os.path.exists(override_path):
        with open(override_path, 'w') as driver_override:
            driver_override.write('\00')
