#!/usr/bin/env python3
import pytest
#import testinfra
#import os
#import testinfra.utils.ansible_runner
import re

#testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
#    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

#BASE_DIR='/package-testing/binary-tarball-tests/pxc/Percona-XtraDB-Cluster-Pro'

def extract_base_dir(host):
    """
    Extracts BASE_DIR from remote /etc/environment.
    """
    env_file = host.file("/etc/environment")
    base_dir = None
    for line in env_file.content_string.splitlines():
        if line.strip().startswith("BASE_DIR="):
            base_dir = re.findall(r'BASE_DIR\s*=\s*[\'"]?([^\'"]+)', line)[0]
            break
    assert base_dir, "BASE_DIR not defined in /etc/environment"
    return base_dir

def test_regular_tarball(host, test_load_env_vars_define_in_test):
    base_dir = extract_base_dir(host)
    cmd = f"cd {base_dir} && ./run.sh"
    result = host.run(cmd)
    print(result.stdout)
    print(result.stderr)
    assert result.rc == 0, result.stderr

def test_minimal_tarball(host, test_load_env_vars_define_in_test):
    with host.sudo():
        cmd = f"sed -i 's|^\(BASE_DIR=.*\)/$|\1-minimal|' /etc/environment"
        result = host.run(cmd)

    base_dir = extract_base_dir(host)
    cmd = f"cd {base_dir} && ./run.sh"
    result = host.run(cmd)
    print(result.stdout)
    print(result.stderr)
    assert result.rc == 0, result.stderr
