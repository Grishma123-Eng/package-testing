#!/usr/bin/env python3
import pytest
import testinfra
import os
import testinfra.utils.ansible_runner

# Get test hosts from Ansible inventory
testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

# Define base directory used in tests
BASE_DIR = '/home/ec2-user/package-testing/binary-tarball-tests/pxc/Percona-XtraDB-Cluster-Pro'

#  FIXTURE: Prepares environment and creates directories
@pytest.fixture(scope='module')
def test_load_env_vars_define_in_test(host):
    with host.sudo():
        # Set BASE_DIR in environment
        host.run(f"echo BASE_DIR={BASE_DIR} >> /etc/environment")

        # Set directory ownership for current group
        user_group = host.run("id -gn").stdout.strip()
        for dir in (
            "/home/ec2-user/package-testing",
            BASE_DIR,
            f"{BASE_DIR}-minimal"
        ):
            host.run(f"mkdir -p {dir}")
            host.run(f"chown -R {user_group}:{user_group} {dir}")
            host.run(f"ls -ld {dir}")

#  Helper function to run the test
def run_tarball_test(host, base_dir_suffix=None, extra_env=""):
    with host.sudo():
        # Change BASE_DIR in environment if suffix is provided
        if base_dir_suffix:
            host.run(f"sed -i 's|^BASE_DIR=.*|BASE_DIR={BASE_DIR}{base_dir_suffix}|' /etc/environment")

        # Add any extra environment variables
        if extra_env:
            for var in extra_env.splitlines():
                host.run(f"echo '{var}' >> /etc/environment")

    # Make sure path exists and run test script
    cmd = f"cd {BASE_DIR} && ./run.sh"
    result = host.run(cmd)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.rc == 0, result.stdout or result.stderr

#  Tests below will auto-trigger the fixture above
def test_regular_tarball(host, test_load_env_vars_define_in_test):
    run_tarball_test(host)

def test_minimal_tarball(host, test_load_env_vars_define_in_test):
    run_tarball_test(host, base_dir_suffix='-minimal')
