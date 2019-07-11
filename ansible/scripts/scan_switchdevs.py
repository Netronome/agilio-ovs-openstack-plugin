#!/usr/bin/python2.7

from __future__ import print_function

import os


def get_phys_switch_id(netdev):
    try:
        with open('/sys/class/net/{}/phys_switch_id'.format(netdev)) as f:
            return f.read().strip()
    except (OSError, IOError):
        return None


def prettiest(x, y):
    if len(x) == len(y):
        return x if x < y else y
    else:
        return x if len(x) < len(y) else y


def find_pf(netdev):
    dev_path = '/sys/class/net/{}/device/net'.format(netdev)
    if not os.path.isdir(dev_path):
        return None
    try:
        candidates = os.listdir(dev_path)
    except (OSError, IOError):
        return None
    for candidate in candidates:
        phys_switch_id = get_phys_switch_id(candidate)
        if not phys_switch_id:
            return candidate
    return reduce(prettiest, candidates)


def main():
    switchdevs = {}
    for netdev in os.listdir('/sys/class/net'):
        switch_id = get_phys_switch_id(netdev)
        if not switch_id:
            continue
        pfname = find_pf(netdev)
        if not pfname:
            continue
        if switch_id in switchdevs:
            switchdevs[switch_id] = prettiest(pfname, switchdevs[switch_id])
        else:
            switchdevs[switch_id] = pfname
    print(str(switchdevs))


if __name__ == '__main__':
    main()
