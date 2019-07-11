#!/bin/sh
ansible-playbook playbook.yaml -i hosts.yaml -v $*
