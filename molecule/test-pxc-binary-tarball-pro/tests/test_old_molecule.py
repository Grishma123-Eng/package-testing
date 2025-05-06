#!/usr/bin/env python3
import pytest
import testinfra
import os
import testinfra.utils.ansible_runner

# Get test hosts from Ansible inventory
testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

# Define base directory used in tests
BASE_DIR = '/package-testing/binary-tarball-tests/pxc/Percona-XtraDB-Cluster-Pro'

#  FIXTURE: Prepares environment and creates directories
@pytest.fixture(scope='module')
def test_load_env_vars_define_in_test(host):
    with host.sudo():
        # Set BASE_DIR in environment
        host.run(f"echo BASE_DIR={BASE_DIR} >> /etc/environment")

        # Set directory ownership for current group
        user_group = host.run("id -gn").stdout.strip()
        for dir in (
            "/package-testing",
            BASE_DIR,
            f"{BASE_DIR}-minimal"
        ):
            host.run(f"mkdir -p {dir}")
            host.run(f"chown -R {user_group}:{user_group} {dir}")
            host.run(f"ls -ld {dir}")

def test_regular_tarball(host, test_load_env_vars_define_in_test):
    cmd = "cd /package-testing/binary-tarball-tests/pxc/Percona-XtraDB-Cluster-Pro && ./run.sh"
    result = host.run(cmd)
    print(result.stdout)
    print(result.stderr)
    assert result.rc == 0, result.stdout

def test_minimal_tarball(host, test_load_env_vars_define_in_test):
    with host.sudo():
        cmd = f"sed -i 's|^\(BASE_DIR=.*\)/$|\1/-minimal|' /etc/environment"
        result = host.run(cmd)
    cmd = "cd /package-testing/binary-tarball-tests/pxc/Percona-XtraDB-Cluster-Pro/ && ./run.sh"
    result = host.run(cmd)
    print(result.stdout)
    print(result.stderr)
    assert result.rc == 0, result.stdout
