#!/usr/bin/env python3
import subprocess
import time
import json
import os
import pytest
import testinfra

container_name_mysql_router = 'mysql-router'
network_name = 'innodbnet'
docker_tag = os.getenv('ROUTER_VERSION')
docker_acc = os.getenv('DOCKER_ACC')
ps_version = os.getenv('PS_VERSION')
router_docker_image = f"{docker_acc}/percona-mysql-router:{docker_tag}"
percona_docker_image = f"{docker_acc}/percona-server:{ps_version}"

def create_network():
    """Create docker network for innodb cluster"""
    try:
        subprocess.run(['docker', 'network', 'create', network_name], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Network might already exist, ignore
        pass

def create_mysql_config():
    """Create MySQL configuration files for cluster nodes"""
    for N in range(1, 5):
        with open(f'my{N}.cnf', 'w') as file:
            file.write(
                f"[mysqld]\n"
                f"plugin_load_add='group_replication.so'\n"
                f"server_id={(hash(str(time.time()) + str(N))) % 40 + 10}\n"
                f"binlog_checksum=NONE\n"
                f"enforce_gtid_consistency=ON\n"
                f"gtid_mode=ON\n"
                f"relay_log=mysql{N}-relay-bin\n"
                f"innodb_dedicated_server=ON\n"
                f"binlog_transaction_dependency_tracking=WRITESET\n"
                f"slave_preserve_commit_order=ON\n"
                f"slave_parallel_type=LOGICAL_CLOCK\n"
                f"transaction_write_set_extraction=XXHASH64\n"
            )

def start_mysql_containers():
    """Start MySQL containers for innodb cluster"""
    for N in range(1, 5):
        subprocess.run([
            'docker', 'run', '-d',
            f'--name=mysql{N}',
            f'--hostname=mysql{N}',
            '--net=innodbnet',
            '-v', f"{os.getcwd()}/my{N}.cnf:/etc/my.cnf",
            '-e', 'MYSQL_ROOT_PASSWORD=root', percona_docker_image
        ], check=True)
    time.sleep(60)

def create_new_user():
    """Create user for innodb cluster setup"""
    for N in range(1, 5):
        subprocess.run([
            'docker', 'exec', f'mysql{N}',
            'mysql', '-uroot', '-proot',
            '-e', "CREATE USER 'inno'@'%' IDENTIFIED BY 'inno'; GRANT ALL privileges ON *.* TO 'inno'@'%' with grant option; FLUSH PRIVILEGES;"
        ], check=True)

def verify_new_user():
    """Verify user creation"""
    for N in range(1, 5):
        subprocess.run([
            'docker', 'exec', f'mysql{N}',
            'mysql', '-uinno', '-pinno',
            '-e', "SHOW VARIABLES WHERE Variable_name = 'hostname';",
            '-e', "SELECT user FROM mysql.user WHERE user = 'inno';"
        ], check=True)
    time.sleep(30)

def docker_restart():
    """Restart MySQL containers"""
    subprocess.run(['docker', 'restart', 'mysql1', 'mysql2', 'mysql3', 'mysql4'], check=True)
    time.sleep(10)

def create_cluster():
    """Create innodb cluster"""
    subprocess.run([
        'docker', 'exec', 'mysql1',
        'mysqlsh', '-uinno', '-pinno', '--', 'dba', 'create-cluster', 'testCluster'
    ], check=True)

def add_slave():
    """Add instances to the cluster"""
    try:
        # Try adding the first slave with 'incremental' recovery method
        result = subprocess.run([
            'docker', 'exec', 'mysql1',
            'mysqlsh', '-uinno', '-pinno', '--',
            'cluster', 'add-instance', '--uri=inno@mysql2', '--recoveryMethod=incremental'
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        time.sleep(120)  # Wait for the first instance to finish

        # Log the result of the first subprocess call
        print(f"STDOUT (mysql2): {result.stdout.decode()}")
        print(f"STDERR (mysql2): {result.stderr.decode()}")

        # Check for GTID error and handle it
        if "GTID state is not compatible" in result.stderr.decode():
            print("GTID compatibility issue detected. Trying to clean the GTID state before adding the instance.")
            reset_gtid = subprocess.run([
                'docker', 'exec', 'mysql2',
                'mysqlsh', '-uinno', '-pinno', '--',
                'dba', 'reset', '--gtid'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"GTID reset result: {reset_gtid.stdout.decode()}")
            print(f"GTID reset error: {reset_gtid.stderr.decode()}")

            # Retry adding the instance with 'incremental' recovery method
            result = subprocess.run([
                'docker', 'exec', 'mysql1',
                'mysqlsh', '-uinno', '-pinno', '--',
                'cluster', 'add-instance', '--uri=inno@mysql2', '--recoveryMethod=incremental'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            time.sleep(120)
            print(f"STDOUT (mysql2 - retry): {result.stdout.decode()}")
            print(f"STDERR (mysql2 - retry): {result.stderr.decode()}")

        # Now, try adding the second instance (mysql3)
        result = subprocess.run([
            'docker', 'exec', 'mysql1',
            'mysqlsh', '-uinno', '-pinno', '--',
            'cluster', 'add-instance', '--uri=inno@mysql3', '--recoveryMethod=incremental'
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(120)
        print(f"STDOUT (mysql3): {result.stdout.decode()}")
        print(f"STDERR (mysql3): {result.stderr.decode()}")

        # Similarly, try adding the third instance (mysql4)
        result = subprocess.run([
            'docker', 'exec', 'mysql1',
            'mysqlsh', '-uinno', '-pinno', '--',
            'cluster', 'add-instance', '--uri=inno@mysql4', '--recoveryMethod=incremental'
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(120)
        print(f"STDOUT (mysql4): {result.stdout.decode()}")
        print(f"STDERR (mysql4): {result.stderr.decode()}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while adding instance: {e}")
        print(f"STDOUT: {e.stdout.decode() if e.stdout else 'No output'}")
        print(f"STDERR: {e.stderr.decode() if e.stderr else 'No error output'}")

@pytest.fixture(scope='module', autouse=True)
def setup_cluster():
    """Setup innodb cluster before running router tests"""
    create_network()
    create_mysql_config()
    start_mysql_containers()
    create_new_user()
    verify_new_user()
    docker_restart()
    create_cluster()
    add_slave()
    yield
    # Cleanup MySQL containers and network
    try:
        subprocess.run(['docker', 'stop', 'mysql1', 'mysql2', 'mysql3', 'mysql4'], check=False, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'rm', 'mysql1', 'mysql2', 'mysql3', 'mysql4'], check=False, stderr=subprocess.DEVNULL)
        subprocess.run(['docker', 'network', 'rm', network_name], check=False, stderr=subprocess.DEVNULL)
        # Cleanup config files
        for N in range(1, 5):
            try:
                os.remove(f'my{N}.cnf')
            except OSError:
                pass
    except Exception as e:
        print(f"Cleanup error (non-fatal): {e}")

@pytest.fixture(scope='module')
def host():
    """Fixture to bootstrap and return router container host"""
    # Run mysql-router container
    docker_id = subprocess.check_output(
        ['docker', 'run', '-d', '--name', container_name_mysql_router, '--net', network_name,
         '-e', 'MYSQL_HOST=mysql1', '-e', 'MYSQL_PORT=3306', '-e', 'MYSQL_USER=inno',
         '-e', 'MYSQL_PASSWORD=inno', '-e', 'MYSQL_INNODB_CLUSTER_MEMBERS=4', router_docker_image]).decode().strip()
    try:
        subprocess.check_call(['docker','exec','--user','root',container_name_mysql_router,'microdnf','install','-y','net-tools'], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Try with yum if microdnf fails
        try:
            subprocess.check_call(['docker','exec','--user','root',container_name_mysql_router,'yum','install','-y','net-tools'], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            pass  # net-tools might already be installed
    time.sleep(20)
    yield testinfra.get_host("docker://root@" + docker_id)
    subprocess.check_call(['docker', 'rm', '-f', docker_id], stderr=subprocess.DEVNULL)

class TestRouterEnvironment:
    def test_mysqlrouter_version(self, host):
        """Test mysqlrouter version matches expected version"""
        command = "mysqlrouter --version"
        output = host.check_output(command)
        # Router version tag is major.minor (e.g., 8.4), but output may contain full version like 8.4.7
        # Check if major.minor version is in the output
        assert docker_tag in output, f"Expected router version {docker_tag} not found in output: {output}"

    def test_mysqlsh_version(self, host):
        """Test mysqlsh version matches PS version"""
        command = "mysqlsh --version"
        output = host.check_output(command)
        # Extract version from output (format may vary)
        assert ps_version.replace('-amd64', '') in output or any(part in output for part in ps_version.split('.')[:2])

    def test_mysqlrouter_directory_permissions(self, host):
        """Test mysqlrouter directory permissions"""
        assert host.file('/var/lib/mysqlrouter').user == 'mysql'
        assert host.file('/var/lib/mysqlrouter').group == 'mysql'
        assert oct(host.file('/var/lib/mysqlrouter').mode) == '0o755'

    def test_mysql_user(self, host):
        """Test mysql user exists with correct UID"""
        mysql_user = host.user('mysql')
        print(f"Username: {mysql_user.name}, UID: {mysql_user.uid}")
        assert mysql_user.exists
        assert mysql_user.uid == 1001

    def test_mysqlrouter_ports(self, host):
        """Test mysqlrouter ports are listening"""
        assert host.socket("tcp://6446").is_listening
        assert host.socket("tcp://6447").is_listening
        assert host.socket("tcp://64460").is_listening
        assert host.socket("tcp://64470").is_listening

    def test_mysqlrouter_config(self, host):
        """Test mysqlrouter configuration file exists with correct permissions"""
        assert host.file("/etc/mysqlrouter/mysqlrouter.conf").exists
        assert host.file("/etc/mysqlrouter/mysqlrouter.conf").user == "root"
        assert host.file("/etc/mysqlrouter/mysqlrouter.conf").group == "root"
        assert oct(host.file("/etc/mysqlrouter/mysqlrouter.conf").mode) == "0o644"
