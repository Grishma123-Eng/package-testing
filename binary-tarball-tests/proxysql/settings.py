#!/usr/bin/env python3
import os
import re
import pytest


def source_environment_file(filepath="/etc/environment"):
    """
    Loads environment variables from a given file into os.environ.

    :param filepath: Path to the environment file (default is /etc/environment).
    """
    try:
        with open(filepath, 'r') as file:
          for line in file:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('\'"')
                os.environ[key] = value
                print(f'{line}')
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"Error while sourcing environment file: {e}")

def set_pro_vars():
    """
    Retrieves and returns environment-based settings for PRO, DEBUG, and FIPS_SUPPORTED.
    """
    source_environment_file()
    proxysql_revision = os.getenv('REVISION')
    proxysql_version = os.getenv('proxysql_VERSION')

    if (os.getenv('PRO')):
        base_dir = os.getenv('BASE_DIR')
        print(f"PRINTING THE PRO VALUE PRO: {pro}")
    else:
      base_dir = os.getenv('BASE_DIR')

    if pro:
      print(f"TRUE PRO VAR WORKING")
    else:
      print(f"FALSE PRO VAR NOT WORKING")

    proxysql57_pkg_version = os.getenv('proxysql57_PKG_VERSION')
    glibc_version = os.getenv('GLIBC_VERSION')
    proxysql_version_percona,proxysql_version_upstream = proxysql_version.split('-')
    proxysql_version_major = proxysql_version_percona.split('.')[0] + '.' + proxysql_version_percona.split('.')[1]
    TARBALL_NAME = os.getenv('TARBALL_NAME')

    return {
        #'debug': debug,
        #'fiproxysql_supported': fiproxysql_supported,
        'revision': revision,
        'proxysql_version': proxysql_version,
        'base_dir': base_dir,
        'proxysql_version_upstream': proxysql_version_upstream,
        'proxysql_version_major': proxysql_version_major,
        'proxysql_version_percona': proxysql_version_percona,
        'proxysql57_pkg_version': proxysql57_pkg_version,
        'wsrep_version': wsrep_version,
        'glibc_version': glibc_version,
        'proxysql_version_pro_percona': proxysql_version_pro_percona,
        'TARBALL_NAME' : TARBALL_NAME
    }

source_environment_file()
proxysql_revision = vars['proxysql_revision']
proxysql_version = vars['proxysql_version']
base_dir = vars['base_dir']
proxysql_version_upstream = vars['proxysql_version_upstream']
proxysql_version_major = vars['proxysql_version_major']
proxysql_version_percona = vars['proxysql_version_percona']
proxysql57_pkg_version = vars['proxysql57_pkg_version']
glibc_version = vars['glibc_version']
TARBALL_NAME = vars['TARBALL_NAME']

if proxysql_version_major == "5.7":
    print(proxysql_version)
    print(proxysql57_pkg_version)
    proxysql57_client_version = proxysql57_pkg_version.split('-')[0] + '-' + proxysql57_pkg_version.split('-')[1][3:]
    proxysql57_server_version_norel = proxysql57_pkg_version.split('-')[0] + '-' + proxysql57_pkg_version.split('-')[1][3:] + '-' + proxysql57_pkg_version.split('-')[2].split('.')[0]
    proxysql57_server_version = proxysql57_pkg_version.split('-')[0] + '-' + proxysql57_pkg_version.split('-')[1] + '-' + proxysql57_pkg_version.split('-')[2].split('.')[0]
    proxysql57_client_version_using = "8.1"

# 8.X
proxysql8x_binaries = [
    'bin/garbd',
    'bin/proxysql_extra/pxb-8.0/bin/xtrabackup', 'bin/proxysql_extra/pxb-8.0/bin/xbcloud',
    'bin/proxysql_extra/pxb-8.0/bin/xbcrypt', 'bin/proxysql_extra/pxb-8.0/bin/xbstream',
    'bin/proxysql_extra/pxb-8.4/bin/xtrabackup', 'bin/proxysql_extra/pxb-8.4/bin/xbcloud',
    'bin/proxysql_extra/pxb-8.4/bin/xbcrypt', 'bin/proxysql_extra/pxb-8.4/bin/xbstream',
    #'bin/proxysql_extra/pxb-8.2/bin/xtrabackup', 'bin/proxysql_extra/pxb-8.2/bin/xbcloud',
  # 'bin/proxysql_extra/pxb-8.2/bin/xbcrypt', 'bin/proxysql_extra/pxb-8.2/bin/xbstream',
    #'bin/proxysql_extra/pxb-8.3/bin/xtrabackup', 'bin/proxysql_extra/pxb-8.3/bin/xbcloud',
    #'bin/proxysql_extra/pxb-8.3/bin/xbcrypt', 'bin/proxysql_extra/pxb-8.3/bin/xbstream',
    'bin/mysql', 'bin/mysqld', 'bin/mysqladmin', 'bin/mysqlbinlog',
    'bin/mysqldump', 'bin/mysqlimport', 'bin/mysqlshow',
    'bin/mysqlslap', 'bin/mysqlcheck', 'bin/mysql_config_editor',
    'bin/mysqlrouter', 'bin/mysqlrouter_passwd', 'bin/mysqlrouter_plugin_info', 'bin/mysql_secure_installation',
    'bin/mysql_tzinfo_to_sql'
  ]
proxysql8x_executables = proxysql8x_binaries + [
    'bin/clustercheck', 'bin/wsrep_sst_common', 'bin/wsrep_sst_xtrabackup-v2',
    'bin/proxysql_extra/pxb-8.0/bin/xbcloud_osenv',
    'bin/proxysql_extra/pxb-8.4/bin/xbcloud_osenv',
    #'bin/proxysql_extra/pxb-8.2/bin/xbcloud_osenv',
    #'bin/proxysql_extra/pxb-8.3/bin/xbcloud_osenv',
    'bin/ps-admin',
    'bin/mysqldumpslow',
    'bin/mysql_config',
  ]
proxysql8x_plugins = (
    ('validate_password','validate_password.so'),
    ('rpl_semi_sync_master','semisync_master.so'),('rpl_semi_sync_slave','semisync_slave.so'),
    ('clone','mysql_clone.so')
  )
proxysql8x_functions = (
    ('version_tokens_show', 'version_token.so', 'STRING'),('version_tokens_edit', 'version_token.so', 'STRING'),
    ('version_tokens_delete', 'version_token.so', 'STRING'),('version_tokens_lock_shared', 'version_token.so', 'INT'),('version_tokens_lock_exclusive', 'version_token.so', 'INT'),
    ('version_tokens_unlock', 'version_token.so', 'INT'),('service_get_read_locks', 'locking_service.so', 'INT'),('service_get_write_locks', 'locking_service.so', 'INT'),
    ('service_release_locks', 'locking_service.so', 'INT')
  )
proxysql8x_files = (
    'lib/libgalera_smm.so', 'lib/libperconaserverclient.a', 'lib/libperconaserverclient.so.21.2.42' ,
    'lib/libmysqlservices.a' ,
    'lib/plugin/auth_pam.so', 'lib/plugin/auth_pam_compat.so', #'lib/plugin/keyring_file.so',
    'lib/plugin/keyring_udf.so'
  )
if glibc_version == '2.35':
    proxysql8x_symlinks = (
   #   ('lib/libcrypto.so', 'lib/private/libcrypto.so.3'),('lib/libgcrypt.so', 'lib/private/libgcrypt.so.20.3.4',),
      ('lib/libperconaserverclient.so', 'lib/libperconaserverclient.so.21.2.42'),('lib/libsasl2.so', 'lib/private/libsasl2.so.3.0.0'),
    #  ('lib/libssl.so', 'lib/private/libssl.so.3'),
      ('lib/libtinfo.so', 'lib/private/libtinfo.so.6.3'),
      ('lib/libaio.so','lib/private/libaio.so.1.0.1'),('lib/libbrotlicommon.so', 'lib/private/libbrotlicommon.so.1.0.9'),
      ('lib/libbrotlidec.so', 'lib/private/libbrotlidec.so.1.0.9'), ('lib/libprocps.so', 'lib/private/libprocps.so.8.0.3'),
      #('lib/librtmp.so', 'lib/private/librtmp.so.1'),
      ('lib/libtirpc.so', 'lib/private/libtirpc.so.3.0.0')
    )
else:
    proxysql8x_symlinks = (
      #   ('lib/libcrypto.so', 'lib/private/libcrypto.so.3'),('lib/libgcrypt.so', 'lib/private/libgcrypt.so.20.3.4',),
       ('lib/libperconaserverclient.so', 'lib/libperconaserverclient.so.21.2.42'),('lib/libsasl2.so', 'lib/private/libsasl2.so.3.0.0'),
    #  ('lib/libssl.so', 'lib/private/libssl.so.3'),
      ('lib/libtinfo.so', 'lib/private/libtinfo.so.6.2'),
      ('lib/libaio.so','lib/private/libaio.so.1.0.1'),('lib/libbrotlicommon.so', 'lib/private/libbrotlicommon.so.1.0.9'),
      ('lib/libbrotlidec.so', 'lib/private/libbrotlidec.so.1.0.9'), ('lib/libprocps.so', 'lib/private/libprocps.so.8.0.3'),
      #('lib/librtmp.so', 'lib/private/librtmp.so.1'), 
      ('lib/libtirpc.so', 'lib/private/libtirpc.so.3.0.0')
    #  ('lib/libcrypto.so','lib/private/libcrypto.so.1.0.2k'), ('lib/libfreebl3.so','lib/private/libfreebl3.so'),
    #  ('lib/libgcrypt.so','lib/private/libgcrypt.so.11.8.2'),
    #  ('lib/libnspr4.so','lib/private/libnspr4.so'),
    #  ('lib/libnss3.so','lib/private/libnss3.so'), ('lib/libnssutil3.so','lib/private/libnssutil3.so'),
    #  ('lib/libperconaserverclient.so','lib/libperconaserverclient.so.24.0.4'), ('lib/libplc4.so','lib/private/libplc4.so'),
    #  ('lib/libplds4.so','lib/private/libplds4.so'), ('lib/libsasl2.so','lib/private/libsasl2.so.3.0.0'),
    #  ('lib/libsmime3.so','lib/private/libsmime3.so'), ('lib/libssl.so','lib/private/libssl.so.1.0.2k'),
    #  ('lib/libssl3.so','lib/private/libssl3.so'), ('lib/libtinfo.so','lib/private/libtinfo.so.5.9'),
    )
proxysql8x_components = (
    ('file://component_encryption_udf'),('file://component_keyring_kmip'),('file://component_keyring_kms'),('file://component_masking_functions'),('file://component_binlog_utils_udf'),('file://component_percona_udf'),('file://component_audit_log_filter'),('file://component_keyring_vault'),('file://component_binlog_uts_udf')
  )

  # 8.0
proxysql80_binaries = [
    'bin/garbd',
    'bin/proxysql_extra/pxb-2.4/bin/xtrabackup', 'bin/proxysql_extra/pxb-2.4/bin/xbcloud',
    'bin/proxysql_extra/pxb-2.4/bin/xbcrypt', 'bin/proxysql_extra/pxb-2.4/bin/xbstream',
    'bin/proxysql_extra/pxb-8.0/bin/xtrabackup', 'bin/proxysql_extra/pxb-8.0/bin/xbcloud',
    'bin/proxysql_extra/pxb-8.0/bin/xbcrypt', 'bin/proxysql_extra/pxb-8.0/bin/xbstream',
    'bin/mysql', 'bin/mysqld', 'bin/mysqladmin', 'bin/mysqlbinlog',
    'bin/mysqldump', 'bin/mysqlimport', 'bin/mysqlshow', #'bin/mysqlpump', 
    'bin/mysqlslap', 'bin/mysqlcheck', 'bin/mysql_config_editor',
    'bin/mysqlrouter', 'bin/mysqlrouter_passwd', 'bin/mysqlrouter_plugin_info', 'bin/mysql_secure_installation', 'bin/mysql_ssl_rsa_setup',
    'bin/mysql_upgrade', 'bin/mysql_tzinfo_to_sql'
  ]
proxysql80_executables = proxysql80_binaries + [
    'bin/clustercheck', 'bin/wsrep_sst_common', 'bin/wsrep_sst_xtrabackup-v2',
    'bin/proxysql_extra/pxb-2.4/bin/xbcloud_osenv',
    'bin/proxysql_extra/pxb-8.0/bin/xbcloud_osenv',
    'bin/ps-admin',
    'bin/mysqldumpslow',
    'bin/mysql_config',
  ]
proxysql80_plugins = (
    ('audit_log','audit_log.so'),('mysql_no_login','mysql_no_login.so'),('validate_password','validate_password.so'),
    ('version_tokens','version_token.so'),('rpl_semi_sync_master','semisync_master.so'),('rpl_semi_sync_slave','semisync_slave.so'),
    ('clone','mysql_clone.so'),('data_masking','data_masking.so')
  )
proxysql80_functions = (
    ('fnv1a_64', 'libfnv1a_udf.so', 'INTEGER'),('fnv_64', 'libfnv_udf.so', 'INTEGER'),('murmur_hash', 'libmurmur_udf.so', 'INTEGER'),
    ('version_tokens_set', 'version_token.so', 'STRING'),('version_tokens_show', 'version_token.so', 'STRING'),('version_tokens_edit', 'version_token.so', 'STRING'),
    ('version_tokens_delete', 'version_token.so', 'STRING'),('version_tokens_lock_shared', 'version_token.so', 'INT'),('version_tokens_lock_exclusive', 'version_token.so', 'INT'),
    ('version_tokens_unlock', 'version_token.so', 'INT'),('service_get_read_locks', 'locking_service.so', 'INT'),('service_get_write_locks', 'locking_service.so', 'INT'),
    ('service_release_locks', 'locking_service.so', 'INT')
  )
proxysql80_files = (
    'lib/libgalera_smm.so', 'lib/libperconaserverclient.a', 'lib/libperconaserverclient.so.21.2.42' ,
    'lib/libmysqlservices.a' , 'lib/plugin/audit_log.so',
    'lib/plugin/auth_pam.so', 'lib/plugin/auth_pam_compat.so', 'lib/plugin/data_masking.so',
    'lib/plugin/data_masking.ini', 'lib/plugin/keyring_file.so',
    'lib/plugin/keyring_udf.so', 'lib/plugin/keyring_vault.so'
  )
if glibc_version == '2.35':
    proxysql80_symlinks = (
        #   ('lib/libcrypto.so', 'lib/private/libcrypto.so.3'),('lib/libgcrypt.so', 'lib/private/libgcrypt.so.20.3.4',),
      ('lib/libperconaserverclient.so', 'lib/libperconaserverclient.so.21.2.42'),('lib/libsasl2.so', 'lib/private/libsasl2.so.2.0.25'),
    #  ('lib/libssl.so', 'lib/private/libssl.so.3'),
      ('lib/libtinfo.so', 'lib/private/libtinfo.so.6.3'),
      ('lib/libaio.so','lib/private/libaio.so.1.0.1'),('lib/libbrotlicommon.so', 'lib/private/libbrotlicommon.so.1.0.9'),
      ('lib/libbrotlidec.so', 'lib/private/libbrotlidec.so.1.0.9'), ('lib/libprocps.so', 'lib/private/libprocps.so.8.0.3'),
      # ('lib/librtmp.so', 'lib/private/librtmp.so.1'),
    )
else:
    proxysql80_symlinks = (
           #   ('lib/libcrypto.so', 'lib/private/libcrypto.so.3'),('lib/libgcrypt.so', 'lib/private/libgcrypt.so.20.3.4',),
      ('lib/libperconaserverclient.so', 'lib/libperconaserverclient.so.21.2.42'),('lib/libsasl2.so', 'lib/private/libsasl2.so.3.0.0'),
    #  ('lib/libssl.so', 'lib/private/libssl.so.3'),
      ('lib/libtinfo.so', 'lib/private/libtinfo.so.6.2'),
      ('lib/libaio.so','lib/private/libaio.so.1.0.1'),('lib/libbrotlicommon.so', 'lib/private/libbrotlicommon.so.1.0.9'),
      ('lib/libbrotlidec.so', 'lib/private/libbrotlidec.so.1.0.9'), ('lib/libprocps.so', 'lib/private/libprocps.so.8.0.3'),
      #('lib/librtmp.so', 'lib/private/librtmp.so.1'), 
     # ('lib/libtirpc.so', 'lib/private/libtirpc.so.3.0.0')
     # ('lib/libcrypto.so','lib/private/libcrypto.so.1.0.2k'), ('lib/libfreebl3.so','lib/private/libfreebl3.so'),

     # ('lib/libgcrypt.so','lib/private/libgcrypt.so.11.8.2'), ('lib/libnspr4.so','lib/private/libnspr4.so'),
    #  ('lib/libnss3.so','lib/private/libnss3.so'), ('lib/libnssutil3.so','lib/private/libnssutil3.so'),
     # ('lib/libperconaserverclient.so','lib/libperconaserverclient.so.21.2.41'), ('lib/libplc4.so','lib/private/libplc4.so'),
      #('lib/libplds4.so','lib/private/libplds4.so'), ('lib/libsasl2.so','lib/private/libsasl2.so.3.0.0'),
      #('lib/libsmime3.so','lib/private/libsmime3.so'), ('lib/libssl.so','lib/private/libssl.so.1.0.2k'),
      #('lib/libssl3.so','lib/private/libssl3.so'), ('lib/libtinfo.so','lib/private/libtinfo.so.5.9'),
    )

  # 5.7
proxysql57_binaries = [
    'bin/garbd', 'bin/innochecksum', 'bin/lz4_decompress', 'bin/my_print_defaults',
    'bin/myisam_ftdump','bin/myisamchk', 'bin/myisamlog', 'bin/myisampack', 'bin/mysql', 'bin/mysql_client_test',
    'bin/mysql_config_editor', 'bin/mysql_install_db', 'bin/mysql_plugin', 'bin/mysql_secure_installation',
    'bin/mysql_ssl_rsa_setup', 'bin/mysql_tzinfo_to_sql', 'bin/mysql_upgrade', 'bin/mysqladmin', 'bin/mysqlbinlog',
    'bin/mysqlcheck', 'bin/mysqld', 'bin/mysqldump',
    'bin/mysqlimport',  'bin/mysqlshow', 'bin/mysqlslap', 'bin/mysqltest', 'bin/mysqlxtest', 'bin/perror' ,'bin/mysqlpump',
    'bin/replace', 'bin/resolve_stack_dump',
    'bin/resolveip',
    'bin/zlib_decompress'
  ]
proxysql57_executables = proxysql57_binaries + [
    'bin/clustercheck',
    'bin/mysql_config',
    'bin/mysqld_multi', 'bin/mysqld_safe', 'bin/mysqldumpslow',
    'bin/ps-admin', 'bin/proxysql_mysqld_helper', 'bin/proxysql_tokudb_admin', 'bin/pyclustercheck',
    'bin/wsrep_sst_common', 'bin/wsrep_sst_mysqldump', 'bin/wsrep_sst_rsync', 'bin/wsrep_sst_xtrabackup-v2',
  ]
proxysql57_plugins = (
    ('audit_log','audit_log.so'),('mysql_no_login','mysql_no_login.so'),('validate_password','validate_password.so'),
    ('version_tokens','version_token.so'),('rpl_semi_sync_master','semisync_master.so'),
    ('rpl_semi_sync_slave','semisync_slave.so')
  )
proxysql57_functions = (
    ('fnv1a_64', 'libfnv1a_udf.so', 'INTEGER'),('fnv_64', 'libfnv_udf.so', 'INTEGER'),('murmur_hash', 'libmurmur_udf.so', 'INTEGER'),
    ('version_tokens_set', 'version_token.so', 'STRING'),('version_tokens_show', 'version_token.so', 'STRING'),('version_tokens_edit', 'version_token.so', 'STRING'),
    ('version_tokens_delete', 'version_token.so', 'STRING'),('version_tokens_lock_shared', 'version_token.so', 'INT'),('version_tokens_lock_exclusive', 'version_token.so', 'INT'),
    ('version_tokens_unlock', 'version_token.so', 'INT'),('service_get_read_locks', 'locking_service.so', 'INT'),('service_get_write_locks', 'locking_service.so', 'INT'),
    ('service_release_locks', 'locking_service.so', 'INT')
  )
proxysql57_files = (
    'lib/libgalera_smm.so', 'lib/libperconaserverclient.a', 'lib/libperconaserverclient.so.20.3.31' ,
    'lib/libmysqlservices.a' , 'lib/libcoredumper.a', 'lib/mysql/plugin/audit_log.so',
    'lib/mysql/plugin/auth_pam.so', 'lib/mysql/plugin/auth_pam_compat.so',
    'lib/mysql/plugin/keyring_file.so', 'lib/mysql/plugin/keyring_udf.so', 'lib/mysql/plugin/keyring_vault.so'
  )
proxysql57_symlinks = (
    ('lib/libperconaserverclient.so', 'lib/libperconaserverclient.so.20.3.31'),
    ('lib/libperconaserverclient.so.20','lib/libperconaserverclient.so.20.3.31'),
  )

  # 5.6
proxysql56_binaries = [
    'bin/mysql', 'bin/mysqld', 'bin/mysqladmin', 'bin/mysqlbinlog', 'bin/mysqldump',
    'bin/mysqlimport', 'bin/mysqlshow', 'bin/mysqlslap', 'bin/mysqlcheck',
    'bin/mysql_config_editor', 'bin/mysql_secure_installation', 'bin/mysql_upgrade', 'bin/mysql_tzinfo_to_sql'
  ]
proxysql56_executables = proxysql56_binaries + [
    'bin/mysqldumpslow'
  ]
proxysql56_plugins = (
    ('audit_log','audit_log.so'),('mysql_no_login','mysql_no_login.so'),('validate_password','validate_password.so'),
    ('rpl_semi_sync_master','semisync_master.so'),('rpl_semi_sync_slave','semisync_slave.so')
  )
proxysql56_functions = (
    ('fnv1a_64', 'libfnv1a_udf.so', 'INTEGER'),('fnv_64', 'libfnv_udf.so', 'INTEGER'),('murmur_hash', 'libmurmur_udf.so', 'INTEGER')
  )
proxysql56_files = (
    'lib/libHotBackup.so', 'lib/libmysqlservices.a',
    'lib/libperconaserverclient.a', 'lib/libperconaserverclient.so.18.1.0' ,'lib/mysql/libjemalloc.so.1',
    'lib/mysql/plugin/ha_tokudb.so', 'lib/mysql/plugin/audit_log.so',
    'lib/mysql/plugin/auth_pam.so', 'lib/mysql/plugin/auth_pam_compat.so', 'lib/mysql/plugin/tokudb_backup.so'
  )
proxysql56_symlinks = (
    ('lib/libperconaserverclient.so.18','lib/libperconaserverclient.so.18.1.0'),('lib/libperconaserverclient.so','lib/libperconaserverclient.so.18.1.0'),
    ('lib/libperconaserverclient_r.a','lib/libperconaserverclient.a'),('lib/libperconaserverclient_r.so','lib/libperconaserverclient.so.18.1.0'),
    ('lib/libperconaserverclient_r.so.18','lib/libperconaserverclient.so.18.1.0'),('lib/libperconaserverclient_r.so.18.1.0','lib/libperconaserverclient.so.18.1.0')
  )
  #####

if re.match(r'^8\.[1-9]$', proxysql_version_major):
      proxysql_binaries = proxysql8x_binaries
      proxysql_executables = proxysql8x_executables
      proxysql_plugins = proxysql8x_plugins
      proxysql_functions = proxysql8x_functions
      proxysql_files = proxysql8x_files
      proxysql_symlinks = proxysql8x_symlinks
      proxysql_components = proxysql8x_components
elif proxysql_version_major == '8.0':
      proxysql_binaries = proxysql80_binaries
      proxysql_executables = proxysql80_executables
      proxysql_plugins = proxysql80_plugins
      proxysql_functions = proxysql80_functions
      proxysql_files = proxysql80_files
      proxysql_symlinks = proxysql80_symlinks
elif proxysql_version_major == '5.7':
      proxysql_binaries = proxysql57_binaries
      proxysql_executables = proxysql57_executables
      proxysql_plugins = proxysql57_plugins
      proxysql_functions = proxysql57_functions
      proxysql_files = proxysql57_files
      proxysql_symlinks = proxysql57_symlinks
elif proxysql_version_major == '5.6':
      proxysql_binaries = proxysql56_binaries
      proxysql_executables = proxysql56_executables
      proxysql_plugins = proxysql56_plugins
      proxysql_functions = proxysql56_functions
      proxysql_files = proxysql56_files
      proxysql_symlinks = proxysql56_symlinks

def get_artifact_sets():
    vars = set_pro_vars()
    proxysql_version_major = vars['proxysql_version_major']
    if re.match(r'^8\.[1-9]$', proxysql_version_major):
        return proxysql8x_executables, proxysql8x_files, proxysql8x_symlinks
    elif proxysql_version_major == '8.0':
        return proxysql80_executables, proxysql80_files, proxysql80_symlinks
    elif proxysql_version_major == '5.7':
        return proxysql57_executables, proxysql57_files, proxysql57_symlinks
    elif proxysql_version_major == '5.6':
        return proxysql56_executables, proxysql56_files, proxysql56_symlinks
    else:
         raise ValueError(f"Unsupported proxysql version: {proxysql_version_major}")