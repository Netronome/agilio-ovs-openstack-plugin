#!/usr/bin/python2

from __future__ import print_function
from subprocess import Popen, PIPE

import argparse
import json
import os


def _cmd(command):
    """Runs command and returns stdout"""
    cmd = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    ret = cmd.communicate()[0]
    stdout = ret.decode(encoding='UTF-8')
    return cmd.returncode, stdout


def _convert_cpulist_to_siblings(cpulist):
    """Converts CORE,SOCKET,CPU tuples to a list of CPU siblings"""
    if len(cpulist) == 0:
        return []
    cpulist = sorted(cpulist)
    all_siblings = []
    current_siblings = []
    sibling_core_socket = cpulist[0][0], cpulist[0][1]
    for cpu in cpulist:
        cpu_core_socket = cpu[0], cpu[1]
        if sibling_core_socket == cpu_core_socket:
            current_siblings.append(cpu[2])
        else:
            all_siblings.append(current_siblings)
            current_siblings = [cpu[2]]
            sibling_core_socket = cpu_core_socket
    all_siblings.append(current_siblings)
    return all_siblings


def get_numa_map():
    """Returns NUMA map of siblings from lscpu output"""
    rc, lscpu_string = _cmd(['lscpu', '-p=NODE,CORE,SOCKET,CPU'])
    if rc != 0:
        return {}
    cpus = []
    numa_nodes = []
    for line in lscpu_string.splitlines():
        if len(line) > 1 and line[0] != '#':
            cpus.append(list(map(int, line.split(','))))
            if cpus[-1][0] not in numa_nodes:
                numa_nodes.append(cpus[-1][0])
    numa_map = {}
    for numa in numa_nodes:
        cpulist = [cpu[1:] for cpu in cpus if cpu[0] == numa]
        numa_map[numa] = _convert_cpulist_to_siblings(cpulist)
    return numa_map


def get_cpu_subset_str(numa_map, start=None, stop=None,
                       numa_nodes=None, omit_siblings=False):
    """Returns comma-delimited subset of CPUs"""
    cpuset = []
    for numa in numa_map.keys():
        if numa_nodes is None or numa in numa_nodes:
            siblings = numa_map[numa][start:stop]
            if omit_siblings:
                filtered_siblings = [i[0] for i in siblings]
            else:
                filtered_siblings = [j for i in siblings for j in i]
            cpuset.extend(filtered_siblings)
    cpuset = sorted(cpuset)
    return ','.join(map(str, cpuset))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system_cores', type=int, default=2,
                        help='Cores per NUMA to reserve'
                             ' for system/os (default: 2)')
    parser.add_argument('--xvio_cores', type=int, default=2,
                        help='Cores per NUMA to allocate'
                             ' to XVIO (default: 2)')
    parser.add_argument('--system_mem_g', type=int, default=8,
                        help='GiB of RAM to reserve'
                             ' for system/os (default: 8)')
    args = parser.parse_args()

    system_cores = args.system_cores
    xvio_cores = args.xvio_cores
    system_mem_g = args.system_mem_g

    numa_map = get_numa_map()
    mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    phys_mem_g = mem_bytes / (1024**3)
    hugepages_2m = (phys_mem_g - system_mem_g) * 512

    output = {}
    output['hugepages_2m'] = hugepages_2m
    output['kernel_isolcpus'] = get_cpu_subset_str(
        numa_map,
        start=system_cores)
    output['xvio_cpus'] = get_cpu_subset_str(
        numa_map,
        start=system_cores,
        stop=system_cores + xvio_cores,
        omit_siblings=True)
    output['nova_vcpupin'] = get_cpu_subset_str(
        numa_map,
        start=system_cores + xvio_cores)
    print(json.dumps(output))


if __name__ == '__main__':
    main()
