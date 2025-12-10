#!/usr/bin/env python3
import pytest
import subprocess
import testinfra
import time
import mysql
from packaging import version

from settings import *

@pytest.fixture(scope='module')
@pytest.fixture(scope='module')
def mysql_server(request, pro_fips_vars):
    fips_supported = pro_fips_vars['fips_supported']
    base_dir = pro_fips_vars['base_dir']
    # Build features list based only on OS-level FIPS support
    features = []
    if fips_supported:
        features.append('fips')
    # Start MySQL with proper environment + flags
    mysql_server = mysql.MySQL(base_dir, features)
    mysql_server.start()
    # Give server a moment to initialize
    time.sleep(10)
    yield mysql_server
    # Cleanup after tests
    mysql_server.purge()

def test_fips_md5(host, mysql_server,pro_fips_vars):
    pro = pro_fips_vars['pro']
    fips_supported = pro_fips_vars['fips_supported']
    debug = pro_fips_vars['debug']
    if not fips_supported:
        pytest.skip("FIPS not supported on this OS")
    query = "SELECT MD5('foo');"
    output = mysql_server.run_query(query)
    print("MD5 Output:", output)
     ssert '00000000000000000000000000000000' in output

def test_fips_value(host,mysql_server,pro_fips_vars):
    fips_supported = pro_fips_vars['fips_supported']
    if not fips_supported:
        pytest.skip("FIPS not supported on this OS")
    query = "SELECT @@ssl_fips_mode;"
    output = mysql_server.run_query(query)
    print("@@ssl_fips_mode:", output)
    assert 'ON' in output

def test_fips_in_log(host, mysql_server,pro_fips_vars):
    fips_supported = pro_fips_vars['fips_supported']
    if not fips_supported:
        pytest.skip("FIPS not supported on this OS")
    with host.sudo():
        query = "SELECT @@log_error;"
        error_log = mysql_server.run_query(query)
        logs = host.check_output(f"head -n30 {error_log}")
        print("Error Log Snippet:\n", logs)
        assert (
            "FIPS-approved version of the OpenSSL cryptographic library" in logs
        )

def test_rocksdb_install(host, mysql_server,pro_fips_vars):
    ps_version_major = pro_fips_vars['ps_version_major']
    if ps_version_major not in ['5.6']:
        host.run(mysql_server.psadmin+' --user=root -S'+mysql_server.socket+' --enable-rocksdb')
        assert mysql_server.check_engine_active('ROCKSDB')
    else:
        pytest.skip('RocksDB is available from 5.7!')

def test_tokudb_install(host, mysql_server,pro_fips_vars):
    ps_version_major = pro_fips_vars['ps_version_major']
    if ps_version_major in ['5.6']:
        host.run('sudo '+mysql_server.psadmin+' --user=root -S'+mysql_server.socket+' --enable --enable-backup')
        mysql_server.restart()
        host.run('sudo '+mysql_server.psadmin+' --user=root -S'+mysql_server.socket+' --enable --enable-backup')
        assert mysql_server.check_engine_active('TokuDB')
    else:
        pytest.skip('TokuDB is skipped from 5.7!')

def test_install_functions(mysql_server):
    for function in ps_functions:
        mysql_server.install_function(function[0], function[1], function[2])

def test_install_component(mysql_server,pro_fips_vars):
    ps_version_major = pro_fips_vars['ps_version_major']
    if ps_version_major == '8.0' or re.match(r'^8\.[1-9]$', ps_version_major):
        for component in ps_components:
            mysql_server.install_component(component)
    else:
        pytest.skip('Component is checked from 8.0!')

def test_install_plugin(mysql_server):
    for plugin in ps_plugins:
        mysql_server.install_plugin(plugin[0], plugin[1])

def test_audit_log_v2(mysql_server,pro_fips_vars):
    ps_version_major = pro_fips_vars['ps_version_major']
    if ps_version_major in ['8.0']:
        query='source {}/share/audit_log_filter_linux_install.sql;'.format(base_dir)
        mysql_server.run_query(query)
        query = 'SELECT plugin_status FROM information_schema.plugins WHERE plugin_name = "audit_log_filter";'
        output = mysql_server.run_query(query)
        assert 'ACTIVE' in output
    else:
        pytest.skip('audit_log_v2 is checked from 8.0!')

def test_telemetry_status(mysql_server,pro_fips_vars):
    ps_version_major = pro_fips_vars['ps_version_major']
    if ps_version_major in ['8.0']:
        # Fetch telemetry settings
        query = "SHOW VARIABLES LIKE '%percona_telemetry%';"
        telemetry_vars = mysql_server.run_query(query)

        # Debug: Print the raw output for inspection
        print("Telemetry Query Output:", telemetry_vars)

        # Convert the output to a dictionary
        telemetry_settings = {}
        lines = telemetry_vars.split('\n')
        for line in lines:
            parts = line.split('\t')
            if len(parts) == 2:
                key, value = parts
                telemetry_settings[key] = value
            else:
                print(f"Skipping line due to insufficient data: {line}")

        # Debug: Print the parsed telemetry settings
        print("Parsed Telemetry Settings:", telemetry_settings)

        # Check if telemetry is disabled
        assert telemetry_settings.get('percona_telemetry_disable') == 'OFF', "Telemetry is enabled"

    else:
        pytest.skip('telemetry agent is checked from 8.0!')
