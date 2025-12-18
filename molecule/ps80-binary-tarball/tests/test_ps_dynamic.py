#!/usr/bin/env python3
import sys
import os

# Prefer the local molecule copy of settings.py first, then fall back to the shared binary-tests path for mysql.py, etc.
local_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'molecule', 'ps80-binary-tarball')
remote_path = '/package-testing/molecule/ps80-binary-tarball/'
local_path_abs = os.path.abspath(local_path)
if os.path.exists(local_path_abs):
    sys.path.insert(0, local_path_abs)
else:
    sys.path.insert(0, remote_path)

import pytest
import subprocess
import testinfra
import time
import mysql
from packaging import version
from settings import *



@pytest.fixture(scope='module')
def mysql_server(request, pro_fips_vars, host):
    fips_supported = pro_fips_vars['fips_supported']
    base_dir = pro_fips_vars['base_dir']

    features = []
    if fips_supported:
        features.append("fips")

    mysql_server = mysql.MySQL(base_dir, features, host=host)
    mysql_server.start()
    time.sleep(10)
    yield mysql_server
    mysql_server.purge()


def test_fips_md5(host, mysql_server, pro_fips_vars):
    if pro_fips_vars['fips_supported']:
        output = mysql_server.run_query("SELECT MD5('foo');")
        assert '00000000000000000000000000000000' in output
    else:
        pytest.skip("FIPS not supported")


def test_fips_value(host, mysql_server, pro_fips_vars):
    if pro_fips_vars['fips_supported']:
        output = mysql_server.run_query("select @@ssl_fips_mode;")
        assert 'ON' in output
    else:
        pytest.skip("FIPS not supported")


def test_fips_in_log(host, mysql_server, pro_fips_vars):
    if not pro_fips_vars['FIPS_SUPPORTED']:
        pytest.skip("FIPS not supported")

    with host.sudo():
        log_file = mysql_server.run_query("SELECT @@log_error;")
        logs = host.check_output(f"head -n30 {log_file}")
        assert "FIPS-approved version of the OpenSSL cryptographic library" in logs


def test_rocksdb_install(host, mysql_server, pro_fips_vars):
    if pro_fips_vars['ps_version_major'] != '5.6':
        host.run(mysql_server.psadmin + ' --user=root -S' + mysql_server.socket + ' --enable-rocksdb')
        assert mysql_server.check_engine_active('ROCKSDB')
    else:
        pytest.skip("RocksDB not available for 5.6")


def test_tokudb_install(host, mysql_server, pro_fips_vars):
    if pro_fips_vars['ps_version_major'] == '5.6':
        host.run('sudo ' + mysql_server.psadmin + ' --user=root -S' + mysql_server.socket + ' --enable --enable-backup')
        mysql_server.restart()
        host.run('sudo ' + mysql_server.psadmin + ' --user=root -S' + mysql_server.socket + ' --enable --enable-backup')
        assert mysql_server.check_engine_active('TokuDB')
    else:
        pytest.skip("TokuDB removed after 5.7")


def test_install_functions(mysql_server):
    for function in ps_functions:
        mysql_server.install_function(*function)


def test_install_component(mysql_server, pro_fips_vars):
    v = pro_fips_vars['ps_version_major']
    if v == '8.0' or v.startswith("8."):
        for component in ps_components:
            mysql_server.install_component(component)
    else:
        pytest.skip("Components only tested for 8.x")


def test_install_plugin(mysql_server):
    for plugin in ps_plugins:
        mysql_server.install_plugin(*plugin)


def test_audit_log_v2(mysql_server, pro_fips_vars):
    if pro_fips_vars['ps_version_major'] == '8.0':
        base_dir = pro_fips_vars['base_dir']
        mysql_server.run_query(f"source {base_dir}/share/audit_log_filter_linux_install.sql;")
        output = mysql_server.run_query(
            'SELECT plugin_status FROM information_schema.plugins WHERE plugin_name = "audit_log_filter";'
        )
        assert 'ACTIVE' in output
    else:
        pytest.skip("Audit log v2 only for 8.0")


def test_telemetry_status(mysql_server, pro_fips_vars):
    if pro_fips_vars['ps_version_major'] != '8.0':
        pytest.skip("Telemetry only tested for 8.0")

    output = mysql_server.run_query("SHOW VARIABLES LIKE '%percona_telemetry%';")
    print("Telemetry raw output:", output)

    telemetry_settings = {}
    for line in output.split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            telemetry_settings[parts[0]] = parts[1]

    print("Parsed telemetry settings:", telemetry_settings)

    assert telemetry_settings.get("percona_telemetry_disable") == "OFF", "Telemetry is enabled"
