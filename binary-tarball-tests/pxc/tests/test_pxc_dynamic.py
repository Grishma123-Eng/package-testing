#!/usr/bin/env python3
import pytest
import subprocess
import testinfra
import os
import re

from settings import *

@pytest.fixture(scope='module')
def mysql_server():
    """Fixture to manage MySQL server instance."""
    mysql_server = MySQL(base_dir)
    mysql_server.start()
    yield mysql_server
    mysql_server.stop()

def test_executables_exist(host):
    """Test if MySQL executables exist and have correct permissions."""
    for executable in pxc_executables:
        file_path = os.path.join(base_dir, executable)
        file = host.file(file_path)
        assert file.exists, f"{file_path} does not exist"
        assert oct(file.mode) == '0o755', f"Incorrect permissions for {file_path}"

def test_mysql_version(host):
    """Verify MySQL version matches expected output."""
    output = host.check_output(f"{base_dir}/bin/mysql --version")
    if pxc_version_major in ['5.7', '5.6']:
        expected_version = f"mysql  Ver 14.14 Distrib {pxc57_client_version}"
        assert re.search(rf'{re.escape(expected_version)}', output), f"Unexpected version: {output}"
    else:
        expected = (
            f"mysql  Ver {pxc_version} for Linux on x86_64 (Percona XtraDB Cluster binary (GPL) "
            f"{pxc_version_percona}, Revision {pxc_revision}, WSREP version {wsrep_version})"
        )
        assert expected in output, f"Version mismatch: expected '{expected}', got '{output}'"

def test_install_functions(mysql_server):
    """Test if PXC functions can be installed."""
    for function in pxc_functions:
        mysql_server.install_function(*function)

def test_install_plugin(mysql_server):
    """Test if PXC plugins can be installed."""
    for plugin in pxc_plugins:
        mysql_server.install_plugin(*plugin)

def test_cluster_size(mysql_server):
    """Check the cluster size is correct."""
    output = mysql_server.run_query('SHOW STATUS LIKE "wsrep_cluster_size";')
    assert output.split('\t')[1].strip() == "3", f"Unexpected cluster size: {output}"
