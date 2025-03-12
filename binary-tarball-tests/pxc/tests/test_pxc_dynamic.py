#!/usr/bin/env python3
import pytest
import subprocess
import testinfra
import mysql
import os

from settings import *

# Ensure correct library paths for OpenSSL
LIBRARY_PATHS = "/usr/lib64:/usr/lib:/usr/local/lib"
os.environ["LD_LIBRARY_PATH"] = LIBRARY_PATHS + ":" + os.environ.get("LD_LIBRARY_PATH", "")

def check_shared_library(binary_path):
    """Check if all shared libraries are present for the given binary."""
    try:
        output = subprocess.check_output(f"ldd {binary_path}", shell=True, universal_newlines=True)
        missing_libs = [line for line in output.split("\n") if "not found" in line]
        
        if missing_libs:
            pytest.fail(f" Missing shared libraries for {binary_path}:\n" + "\n".join(missing_libs))
    except subprocess.CalledProcessError:
        pytest.fail(f" Failed to check shared libraries for {binary_path}")

@pytest.fixture(scope='module')
def mysql_server(request):
    """Start MySQL server before running tests."""
    mysql_server = mysql.MySQL(base_dir)
    
    # Validate required shared libraries for mysqld
    check_shared_library(mysql_server.mysqld)

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