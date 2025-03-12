#!/usr/bin/env python3
import pytest
import subprocess
import testinfra
import mysql
import os

from settings import *

@pytest.fixture(scope='module')
def mysql_server(request):
    """ Start MySQL server before running tests """

    mysqld_path = os.path.join(base_dir, "bin", "mysqld")

    # Ensure mysqld binary exists
    if not os.path.exists(mysqld_path):
        pytest.fail(f" ERROR: mysqld binary not found at {mysqld_path}")

    # Ensure mysqld is executable
    if not os.access(mysqld_path, os.X_OK):
        os.chmod(mysqld_path, 0o755)

    # Ensure required shared libraries exist
    try:
        output = subprocess.check_output(f"ldd {mysqld_path}", shell=True, universal_newlines=True)
        missing_libs = [line for line in output.split("\n") if "not found" in line]
        if missing_libs:
            pytest.fail(f" Missing shared libraries:\n" + "\n".join(missing_libs))
    except subprocess.CalledProcessError:
        pytest.fail(f" Failed to check shared libraries for {mysqld_path}")

     # Start MySQL Server
    mysql_server = mysql.MySQL(base_dir)
    mysql_server.start()
    yield mysql_server
    mysql_server.stop()



def test_install_functions(mysql_server):
    for function in pxc_functions:
        mysql_server.install_function(function[0], function[1], function[2])

def test_install_plugin(mysql_server):
    for plugin in pxc_plugins:
        mysql_server.install_plugin(plugin[0], plugin[1])

def test_cluster_size(mysql_server):
    output = mysql_server.run_query('SHOW STATUS LIKE "wsrep_cluster_size";')
    assert output.split('\t')[1].strip() == "3"