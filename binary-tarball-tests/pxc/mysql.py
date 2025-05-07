#!/usr/bin/env python3
import subprocess
import re
import os
import time
import shlex
import pytest
from settings import *

def retry(func, times, wait):
    for _ in range(times):
        try:
            func()
            break
        except AssertionError:
            time.sleep(wait)
    else:
        func()

class MySQL:
    def __init__(self, base_dir):
        self.basedir = base_dir
        self.node1_cnf = base_dir+'/node1.cnf'
        self.node2_cnf = base_dir+'/node2.cnf'
        self.node3_cnf = base_dir+'/node3.cnf'
        self.node1_datadir = base_dir+'/node1'
        self.node2_datadir = base_dir+'/node2'
        self.node3_datadir = base_dir+'/node3'
        self.node1_socket = '/tmp/node1_mysql.sock'
        self.node2_socket = '/tmp/node2_mysql.sock'
        self.node3_socket = '/tmp/node3_mysql.sock'
        self.node1_logfile = base_dir+'/log/node1.err'
        self.node2_logfile = base_dir+'/log/node2.err'
        self.node3_logfile = base_dir+'/log/node3.err'
        self.mysql = base_dir+'/bin/mysql'
        self.mysqld = base_dir+'/bin/mysqld'
        self.mysqladmin = base_dir+'/bin/mysqladmin'
        self.pidfile = base_dir+'/mysql.pid'
        self.mysql_install_db = base_dir+'/scripts/mysql_install_db'
        self.wsrep_provider = base_dir+'/lib/libgalera_smm.so'

        # Clean up previous runs
        subprocess.call(['rm', '-Rf', self.node1_datadir])
        subprocess.call(['rm', '-Rf', self.node2_datadir])
        subprocess.call(['rm', '-Rf', self.node3_datadir])
        subprocess.call(['rm', '-f', self.node1_logfile])
        subprocess.call(['rm', '-f', self.node2_logfile])
        subprocess.call(['rm', '-f', self.node3_logfile])
        subprocess.call(['rm', '-f', self.node1_cnf])
        subprocess.call(['rm', '-f', self.node2_cnf])
        subprocess.call(['rm', '-f', self.node3_cnf])
        subprocess.call(['mkdir', '-p', self.basedir+'/log'])
        
        # Create configuration files
        self._create_config_files()

        output = subprocess.check_output([self.mysqld, '--version'], universal_newlines=True)
        x = re.search(r"[0-9]+\.[0-9]+", output)
        self.major_version = x.group()
        if self.major_version != "8.0" and not re.match(r'^8\.[1-9]$', pxc_version_major):
            self.sst_opts = ["--wsrep_sst_method=xtrabackup-v2", "--wsrep_sst_auth=root:"]
        else:
            self.sst_opts = ["--wsrep_sst_method=xtrabackup-v2"]
        
        # Initialize data directories
        if self.major_version == "5.6":
            subprocess.check_call([self.mysql_install_db, '--no-defaults', '--basedir=' + self.basedir,
                                 '--datadir='+ self.node1_datadir])
            subprocess.check_call([self.mysql_install_db, '--no-defaults', '--basedir=' + self.basedir,
                                 '--datadir=' + self.node2_datadir])
            subprocess.check_call([self.mysql_install_db, '--no-defaults', '--basedir=' + self.basedir,
                                 '--datadir=' + self.node3_datadir])
        else:
            self.psadmin = base_dir+'/bin/ps-admin'
            subprocess.check_call([self.mysqld, '--no-defaults', '--initialize-insecure', '--basedir=' + self.basedir,
                                 '--datadir=' + self.node1_datadir])
            subprocess.check_call([self.mysqld, '--no-defaults', '--initialize-insecure', '--basedir=' + self.basedir,
                                 '--datadir=' + self.node2_datadir])
            subprocess.check_call([self.mysqld, '--no-defaults', '--initialize-insecure', '--basedir=' + self.basedir,
                                 '--datadir=' + self.node3_datadir])

    def _create_config_files(self):
        """Create configuration files for all nodes"""
        common_config = f"""
[mysqld]
basedir={self.basedir}
wsrep_provider={self.wsrep_provider}
wsrep_sst_method=xtrabackup-v2
wsrep_cluster_address=gcomm://
binlog_format=ROW
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2
wsrep_slave_threads=8
wsrep_debug=1
wsrep_provider_options=\"socket.ssl=no\"
"""

        # Node 1 configuration (bootstrap node)
        node1_config = f"""{common_config}
datadir={self.node1_datadir}
socket={self.node1_socket}
port=3306
wsrep_node_address=127.0.0.1:5010
wsrep_node_name=node1
log-error={self.node1_logfile}
pid-file={self.basedir}/node1.pid
"""

        # Node 2 configuration
        node2_config = f"""{common_config}
datadir={self.node2_datadir}
socket={self.node2_socket}
port=3307
wsrep_node_address=127.0.0.1:5011
wsrep_node_name=node2
log-error={self.node2_logfile}
pid-file={self.basedir}/node2.pid
wsrep_cluster_address=gcomm://127.0.0.1:5010
"""

        # Node 3 configuration
        node3_config = f"""{common_config}
datadir={self.node3_datadir}
socket={self.node3_socket}
port=3308
wsrep_node_address=127.0.0.1:5012
wsrep_node_name=node3
log-error={self.node3_logfile}
pid-file={self.basedir}/node3.pid
wsrep_cluster_address=gcomm://127.0.0.1:5010,127.0.0.1:5011
"""

        # Write config files
        with open(self.node1_cnf, 'w') as f:
            f.write(node1_config)
        with open(self.node2_cnf, 'w') as f:
            f.write(node2_config)
        with open(self.node3_cnf, 'w') as f:
            f.write(node3_config)

    def startup_check(self, socket):
        """Check if MySQL server is running and ready to accept connections"""
        ping_query = self.basedir + '/bin/mysqladmin --user=root --socket=' + socket + ' ping > /dev/null 2>&1'
        for _ in range(120):
            ping_check = subprocess.call(ping_query, shell=True, stderr=subprocess.DEVNULL)
            if ping_check == 0:
                return True
            time.sleep(1)
        
        # If we get here, the server didn't start
        # Fix the node number extraction from socket path
        node_num = socket.split('_')[0][-1]  # Gets '1' from '/tmp/node1_mysql.sock'
        
        # Use proper attribute name based on node number
        logfile_attr = f'node{node_num}_logfile'
        if not hasattr(self, logfile_attr):
            raise RuntimeError(f"MySQL server failed to start. Log file attribute {logfile_attr} not found.")
        
        logfile = getattr(self, logfile_attr)
        try:
            with open(logfile, 'r') as f:
                logs = f.read()
            raise RuntimeError(f"MySQL server failed to start. Logs:\n{logs}")
        except FileNotFoundError:
            raise RuntimeError(f"MySQL server failed to start and no log file found at {logfile}")

    def start(self):
        """Start the MySQL cluster nodes"""
        # Start bootstrap node (node1)
        subprocess.Popen([self.mysqld, '--defaults-file=' + self.node1_cnf, '--basedir=' + self.basedir,
                         '--datadir=' + self.node1_datadir, '--tmpdir=' + self.node1_datadir,
                         '--socket=' + self.node1_socket, '--log-error=' + self.node1_logfile,
                         '--wsrep_provider=' + self.wsrep_provider, *self.sst_opts, '--wsrep-new-cluster'],
                        env=os.environ)
        
        if not self.startup_check(self.node1_socket):
            raise RuntimeError("Failed to start bootstrap node (node1)")
        
        # Get cluster address from node1
        cluster_address = "gcomm://127.0.0.1:5010"
        
        # Start node2
        subprocess.Popen([self.mysqld, '--defaults-file=' + self.node2_cnf, '--basedir=' + self.basedir,
                         '--datadir=' + self.node2_datadir, '--tmpdir=' + self.node2_datadir,
                         '--socket=' + self.node2_socket, '--log-error=' + self.node2_logfile,
                         '--wsrep_provider=' + self.wsrep_provider, *self.sst_opts,
                         f'--wsrep_cluster_address={cluster_address}'],
                        env=os.environ)
        
        if not self.startup_check(self.node2_socket):
            raise RuntimeError("Failed to start node2")
        
        # Update cluster address for node3
        cluster_address = "gcomm://127.0.0.1:5010,127.0.0.1:5011"
        
        # Start node3
        subprocess.Popen([self.mysqld, '--defaults-file=' + self.node3_cnf, '--basedir=' + self.basedir,
                         '--datadir=' + self.node3_datadir, '--tmpdir=' + self.node3_datadir,
                         '--socket=' + self.node3_socket, '--log-error=' + self.node3_logfile,
                         '--wsrep_provider=' + self.wsrep_provider, *self.sst_opts,
                         f'--wsrep_cluster_address={cluster_address}'],
                        env=os.environ)
        
        if not self.startup_check(self.node3_socket):
            raise RuntimeError("Failed to start node3")

    def stop(self):
        """Stop all MySQL nodes"""
        try:
            subprocess.check_call([self.mysqladmin, '-uroot', '-S'+self.node3_socket, 'shutdown'])
        except subprocess.CalledProcessError:
            print("Warning: Failed to shutdown node3")
        
        try:
            subprocess.check_call([self.mysqladmin, '-uroot', '-S'+self.node2_socket, 'shutdown'])
        except subprocess.CalledProcessError:
            print("Warning: Failed to shutdown node2")
        
        try:
            subprocess.check_call([self.mysqladmin, '-uroot', '-S'+self.node1_socket, 'shutdown'])
        except subprocess.CalledProcessError:
            print("Warning: Failed to shutdown node1")

    def restart(self):
        """Restart the entire cluster"""
        self.stop()
        self.start()

    def run_query(self, query, node="node1"):
        """Execute a SQL query on the specified node"""
        node_sockets = {
            "node1": self.node1_socket,
            "node2": self.node2_socket,
            "node3": self.node3_socket,
        }
        socket = node_sockets[node]

        command = self.mysql+' --user=root -S'+socket+' -s -N -e '+shlex.quote(query)
        try:
            return subprocess.check_output(command, shell=True, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Query failed: {e.output}")

    def install_function(self, fname, soname, return_type):
        """Install a MySQL function"""
        query = 'CREATE FUNCTION {} RETURNS {} SONAME "{}";'.format(fname, return_type, soname)
        self.run_query(query)
        
        query = 'SELECT name FROM mysql.func WHERE dl = "{}";'.format(soname)
        def _assert_function():
            output = self.run_query(query, node="node2")
            assert fname in output
        retry(_assert_function, times=5, wait=0.2)

    def install_plugin(self, pname, soname):
        """Install a MySQL plugin"""
        query = 'INSTALL PLUGIN {} SONAME "{}";'.format(pname, soname)
        self.run_query(query)
        
        query = 'SELECT plugin_status FROM information_schema.plugins WHERE plugin_name = "{}";'.format(pname)
        def _assert_plugin():
            output = self.run_query(query, node="node3")
            assert 'ACTIVE' in output
        retry(_assert_plugin, times=5, wait=0.2)

    def test_install_component(self, cmpt):
        """Test component installation (MySQL 8.0+)"""
        if pxc_version_major == '8.0' or re.match(r'^8\.[1-9]$', pxc_version_major):
            query = f'INSTALL COMPONENT \'{cmpt}\';'
            self.run_query(query)
            
            query = f'SELECT component_urn FROM mysql.component WHERE component_urn = \'{cmpt}\';'
            
            def _assert_plugin():
                output = self.run_query(query, node="node3")
                assert cmpt in output
            retry(_assert_plugin, times=5, wait=0.2)
        else:
            pytest.mark.skip('Components are available from 8.0 onwards')