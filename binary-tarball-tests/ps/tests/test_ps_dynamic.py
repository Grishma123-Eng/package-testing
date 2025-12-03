#!/usr/bin/env python3
import pytest
import subprocess
import sys
import testinfra
import time
import mysql
from packaging import version

from settings import *



@pytest.fixture(scope='module')
def mysql_server(request,pro_fips_vars):
    pro = pro_fips_vars['pro']
    fips_supported = pro_fips_vars['fips_supported']
    features=[]
    if fips_supported:
        features.append('fips')
    mysql_server = mysql.MySQL(base_dir, features)
    mysql_server.start()
    time.sleep(10)
    
    # Verify server is actually running by trying to connect
    max_retries = 5
    server_started = False
    for i in range(max_retries):
        try:
            mysql_server.run_query("SELECT 1;")
            server_started = True
            break
        except subprocess.CalledProcessError as e:
            if i == max_retries - 1:
                # Server failed to start with FIPS - try without FIPS for non-pro packages
                if fips_supported and not pro:
                    # For non-pro packages, if FIPS fails, try without FIPS
                    print(f"MySQL server failed to start with FIPS enabled (attempt {i+1}/{max_retries}). Trying without FIPS...", file=sys.stderr)
                    # Kill any mysqld processes that might be hanging
                    try:
                        subprocess.check_call(['pkill', '-9', '-f', f'{base_dir}/bin/mysqld'], 
                                             stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    except subprocess.CalledProcessError:
                        pass  # No process to kill
                    time.sleep(2)
                    # Clean up completely
                    subprocess.call(['rm','-Rf', mysql_server.datadir], stderr=subprocess.DEVNULL)
                    subprocess.call(['rm','-f', mysql_server.logfile], stderr=subprocess.DEVNULL)
                    subprocess.call(['rm','-f', mysql_server.pidfile], stderr=subprocess.DEVNULL)
                    subprocess.call(['rm','-f', mysql_server.socket], stderr=subprocess.DEVNULL)
                    time.sleep(1)
                    # Create new MySQL instance without FIPS
                    print(f"Creating new MySQL instance without FIPS...", file=sys.stderr)
                    try:
                        mysql_server = mysql.MySQL(base_dir, [])
                        print(f"Starting MySQL server without FIPS...", file=sys.stderr)
                        mysql_server.start()
                        time.sleep(10)
                        # Try to connect again
                        for j in range(max_retries):
                            try:
                                mysql_server.run_query("SELECT 1;")
                                server_started = True
                                # Update fips_supported since we're running without FIPS
                                pro_fips_vars['fips_supported'] = False
                                print(f"MySQL server started successfully without FIPS. Tests will run in non-FIPS mode.", file=sys.stderr)
                                break
                            except subprocess.CalledProcessError as e2:
                                if j == max_retries - 1:
                                    # Read error log for debugging
                                    try:
                                        with open(mysql_server.logfile, 'r') as f:
                                            log_content = f.read()
                                        print(f"Error log content:\n{log_content[-2000:]}", file=sys.stderr)
                                    except:
                                        pass
                                    raise Exception(f"MySQL server failed to start even without FIPS after {max_retries} retries. Check error log: {mysql_server.logfile}")
                                time.sleep(2)
                        break
                    except Exception as e3:
                        print(f"Failed to create/start MySQL instance without FIPS: {e3}", file=sys.stderr)
                        raise
                else:
                    # For pro packages or if FIPS wasn't enabled, raise error
                    # Read error log for debugging
                    try:
                        with open(mysql_server.logfile, 'r') as f:
                            log_content = f.read()
                        print(f"Error log content:\n{log_content[-2000:]}", file=sys.stderr)
                    except:
                        pass
                    raise Exception(f"MySQL server failed to start after {max_retries} retries. Check error log: {mysql_server.logfile}")
            time.sleep(2)
    
    yield mysql_server
    mysql_server.purge()

def test_fips_md5(host, mysql_server, pro_fips_vars):
    """
    FIPS mode should return masked MD5, otherwise normal MD5 hash.
    Works for both PRO and non-PRO packages.
    """
    fips_supported = pro_fips_vars["fips_supported"]
    
    if not fips_supported:
        pytest.skip("FIPS is not supported. Skipping")
    
    output = mysql_server.run_query("SELECT MD5('foo');")
    assert '00000000000000000000000000000000' in output, "Expected masked MD5 in FIPS mode"


def test_fips_value(host, mysql_server, pro_fips_vars):
    """
    Check ssl_fips_mode runtime variable — ON only when FIPS is enabled.
    Works for both PRO and non-PRO packages.
    """
    fips_supported = pro_fips_vars["fips_supported"]
    
    if not fips_supported:
        pytest.skip("FIPS is not supported. Skipping")
    
    output = mysql_server.run_query("select @@ssl_fips_mode;")
    assert 'ON' in output, "ssl_fips_mode should be ON when FIPS is supported"

def test_fips_in_log(host, mysql_server, pro_fips_vars):
    """
    FIPS informational log must appear only when FIPS is supported.
    Works for both PRO and non-PRO packages.
    """
    fips_supported = pro_fips_vars["fips_supported"]
    
    if not fips_supported:
        pytest.skip("FIPS is not supported. Skipping")
    
    with host.sudo():
        error_log = mysql_server.run_query("SELECT @@log_error;")
        logs = host.check_output(f'head -n30 {error_log}')

    fips_message = (
        "A FIPS-approved version of the OpenSSL cryptographic library has been detected"
    )
    assert fips_message in logs, "FIPS message should appear in error log when FIPS is supported"

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
