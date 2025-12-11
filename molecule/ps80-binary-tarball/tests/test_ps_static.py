#!/usr/bin/env python3
import sys
import os
# Add path for both local (test collection) and remote (test execution) scenarios
local_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'binary-tarball-tests', 'ps')
remote_path = '/package-testing/binary-tarball-tests/ps'
local_path_abs = os.path.abspath(local_path)
if os.path.exists(local_path_abs):
    sys.path.insert(0, local_path_abs)
else:
    sys.path.insert(0, remote_path)
import pytest
import testinfra

from settings import *

def test_executables_exist(host,pro_fips_vars):
    base_dir = pro_fips_vars['base_dir']
    for executable in ps_executables:
        assert host.file(base_dir+'/'+executable).exists
        assert oct(host.file(base_dir+'/'+executable).mode) == '0o755'

def test_binaries_version(host,pro_fips_vars):
    pro = pro_fips_vars['pro']
    fips_supported = pro_fips_vars['fips_supported']
    ps_version_major = pro_fips_vars['ps_version_major']
    base_dir = pro_fips_vars['base_dir']
    ps_version = pro_fips_vars['ps_version']
    ps_revision = pro_fips_vars['ps_revision']
    debug = pro_fips_vars['debug']
    ps_version_percona = pro_fips_vars['ps_version_percona']
    base_dir_debug = base_dir + debug


    if ps_version_major in ['5.7', '5.6']:
        # Older versions without Pro support
        assert 'mysql  Ver 14.14 Distrib ' + ps_version + ', for Linux (x86_64)' in host.check_output(
            base_dir + '/bin/mysql --version'
        )
        assert 'mysqld  Ver ' + ps_version + ' for Linux on x86_64 (Percona Server (GPL), Release ' + ps_version_percona + ', Revision ' + ps_revision + ')' in host.check_output(
            base_dir + '/bin/mysqld --version'
        )
    else:
        if pro:
            if os.getenv('DEBUG') == "yes":
                # Newer versions with Pro support
                expected_mysql_output = (
                    f"{base_dir}/bin/mysql  Ver {ps_version}-pro for Linux on x86_64 (Percona Server Pro (GPL), "
                    f"Release {ps_version_percona}, Revision {ps_revision})"
                )
                expected_mysqld_output = (
                    f"{base_dir}/bin/mysqld  Ver {ps_version}-pro for Linux on x86_64 (Percona Server Pro (GPL), "
                    f"Release {ps_version_percona}, Revision {ps_revision})"
                )
            else:
                ps_revision_pro = str(ps_revision) + "-pro"
                # Newer versions with Pro support
                expected_mysql_output = (
                    f"{base_dir}/bin/mysql  Ver {ps_version}-pro for Linux on x86_64 (Percona Server Pro (GPL), "
                    f"Release {ps_version_percona}, Revision {ps_revision})"
                )
                expected_mysqld_output = (
                    f"{base_dir}/bin/mysqld  Ver {ps_version}-pro for Linux on x86_64 (Percona Server Pro (GPL), "
                    f"Release {ps_version_percona}, Revision {ps_revision})"
                )
        else: 
            # Newer versions with Pro support
            expected_mysql_output = (
                f"{base_dir}/bin/mysql  Ver {ps_version} for Linux on x86_64 (Percona Server (GPL), "
                f"Release {ps_version_percona}, Revision {ps_revision})"
            )
            expected_mysqld_output = (
                f"{base_dir}/bin/mysqld  Ver {ps_version} for Linux on x86_64 (Percona Server (GPL), "
                f"Release {ps_version_percona}, Revision {ps_revision})"
            )

        # Assert outputs dynamically
        assert expected_mysql_output in host.check_output(base_dir + '/bin/mysql --version')
        assert expected_mysqld_output in host.check_output(base_dir + '/bin/mysqld --version')

def test_files_exist(host,pro_fips_vars):
    base_dir = pro_fips_vars['base_dir']
    for f in ps_files:
        assert host.file(base_dir+'/'+f).exists
        assert host.file(base_dir+'/'+f).size != 0

def test_symlinks(host,pro_fips_vars):
    base_dir = pro_fips_vars['base_dir']
    for symlink in ps_symlinks:
        assert host.file(base_dir+'/'+symlink[0]).is_symlink
        assert host.file(base_dir+'/'+symlink[0]).linked_to == base_dir+'/'+symlink[1]
        assert host.file(base_dir+'/'+symlink[1]).exists

def test_binaries_linked_libraries(host,pro_fips_vars):
    base_dir = pro_fips_vars['base_dir']
    for binary in ps_binaries:
        assert '=> not found' not in host.check_output('ldd ' + base_dir + '/' + binary)

def test_pro_openssl_files_not_exist(host,pro_fips_vars):
    pro = pro_fips_vars['pro']
    fips_supported = pro_fips_vars['fips_supported']
    base_dir = pro_fips_vars['base_dir']
    if pro:
        for openssl_file in ps_openssl_files:
            assert not host.file(base_dir+'/'+openssl_file).exists
    else:
        pytest.skip("This test is only for PRO tarballs. Skipping")


def test_pro_openssl_files_linked(host,pro_fips_vars):
    pro = pro_fips_vars['pro']
    fips_supported = pro_fips_vars['fips_supported']
    base_dir = pro_fips_vars['base_dir']
    if pro:
        for binary in ps_binaries:
            shared_files = host.check_output('ldd ' + base_dir + '/' + binary)
            for line in shared_files.splitlines():
                for file_name in ['libcrypto.so', 'libssl.so']:
                    if file_name in line:
                        assert not base_dir in line
                        assert not '=> not found' in line
    else:
        pytest.skip("This test is only for PRO tarballs. Skipping")
