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
    # Check if network already exists
    result = subprocess.run(['docker', 'network', 'ls', '--filter', f'name={network_name}', '--format', '{{.Name}}'], 
                           check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if network_name not in result.stdout.decode():
        subprocess.run(['docker', 'network', 'create', network_name], check=True)

def create_mysql_config():
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

def wait_for_mysql_ready(container_name, max_attempts=120):
    """Wait for MySQL container to be ready"""
    # First, wait for container to be running
    for attempt in range(30):
        if check_container_running(container_name):
            break
        time.sleep(1)
    else:
        # Container not running, check status
        result = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                               check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = result.stdout.decode().strip()
        if status:
            print(f"Container {container_name} status: {status}")
        # Try to get logs
        try:
            logs = subprocess.check_output(['docker', 'logs', '--tail', '50', container_name], 
                                         stderr=subprocess.STDOUT).decode()
            print(f"Container {container_name} logs:\n{logs}")
        except Exception as e:
            print(f"Could not get logs for {container_name}: {e}")
        return False
    
    # Now wait for MySQL to be ready
    for attempt in range(max_attempts):
        try:
            # Check if container is still running
            if not check_container_running(container_name):
                print(f"Container {container_name} stopped running")
                return False
            
            result = subprocess.run([
                'docker', 'exec', container_name,
                'mysql', '-uroot', '-proot', '-e', 'SELECT 1'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            if result.returncode == 0:
                return True
            elif attempt % 10 == 0:  # Print progress every 10 attempts
                print(f"Waiting for MySQL in {container_name} to be ready (attempt {attempt + 1}/{max_attempts})...")
        except subprocess.TimeoutExpired:
            print(f"Timeout waiting for MySQL in {container_name}")
        except Exception as e:
            if attempt % 10 == 0:
                print(f"Error checking MySQL in {container_name}: {e}")
        time.sleep(2)
    
    # If we get here, MySQL didn't become ready - get logs
    print(f"MySQL in {container_name} did not become ready after {max_attempts * 2} seconds")
    try:
        logs = subprocess.check_output(['docker', 'logs', '--tail', '100', container_name], 
                                     stderr=subprocess.STDOUT).decode()
        print(f"Container {container_name} logs:\n{logs}")
    except Exception as e:
        print(f"Could not get logs for {container_name}: {e}")
    return False

def check_container_running(container_name):
    """Check if container is running"""
    result = subprocess.run([
        'docker', 'ps', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'
    ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode().strip()
    return container_name in output

def start_mysql_containers():
    for N in range(1, 5):
        container_name = f'mysql{N}'
        print(f"Starting container {container_name}...")
        try:
            subprocess.run([
                'docker', 'run', '-d',
                f'--name={container_name}',
                f'--hostname={container_name}',
                '--net=innodbnet',
                '-v', f"{os.getcwd()}/my{N}.cnf:/etc/my.cnf",
                '-e', 'MYSQL_ROOT_PASSWORD=root', percona_docker_image
            ], check=True)
            print(f"Container {container_name} started, waiting for MySQL to be ready...")
            # Give container a moment to start
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Failed to start container {container_name}: {e}")
            raise
        
        # Wait for each container to be ready
        if not wait_for_mysql_ready(container_name):
            # Get container status before raising error
            result = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                                   check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status = result.stdout.decode().strip()
            raise RuntimeError(f"Container {container_name} failed to become ready. Status: {status}")
        print(f"Container {container_name} is ready!")

def create_new_user():
    for N in range(1, 5):
        container_name = f'mysql{N}'
        # Check if container is running
        if not check_container_running(container_name):
            raise RuntimeError(f"Container {container_name} is not running")
        # Wait for MySQL to be ready
        if not wait_for_mysql_ready(container_name):
            raise RuntimeError(f"MySQL in {container_name} is not ready")
        subprocess.run([
            'docker', 'exec', container_name,
            'mysql', '-uroot', '-proot',
            '-e', "CREATE USER 'inno'@'%' IDENTIFIED BY 'inno'; GRANT ALL privileges ON *.* TO 'inno'@'%' with grant option; FLUSH PRIVILEGES;"
        ], check=True)

def verify_new_user():
    for N in range(1, 5):
        container_name = f'mysql{N}'
        # Check if container is running
        if not check_container_running(container_name):
            raise RuntimeError(f"Container {container_name} is not running")
        # Wait for MySQL to be ready
        if not wait_for_mysql_ready(container_name):
            raise RuntimeError(f"MySQL in {container_name} is not ready")
        subprocess.run([
            'docker', 'exec', container_name,
            'mysql', '-uinno', '-pinno',
            '-e', "SHOW VARIABLES WHERE Variable_name = 'hostname';",
            '-e', "SELECT user FROM mysql.user WHERE user = 'inno';"
        ], check=True)
    time.sleep(30)

def docker_restart():
    subprocess.run(['docker', 'restart', 'mysql1', 'mysql2', 'mysql3', 'mysql4'], check=True)
    time.sleep(10)

def create_cluster():
    subprocess.run([
        'docker', 'exec', 'mysql1',
        'mysqlsh', '-uinno', '-pinno', '--', 'dba', 'create-cluster', 'testCluster'
    ], check=True)

def add_slave():
    try:
        # Try adding the first slave with 'incremental' recovery method
        result = subprocess.run([
            'docker', 'exec', 'mysql1',
            'mysqlsh', '-uinno', '-pinno', '--',
            'cluster', 'add-instance', '--uri=inno@mysql2', '--recoveryMethod=increamental'
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        time.sleep(120)  # Wait for the first instance to finish

        # Log the result of the first subprocess call
        print(f"STDOUT (mysql2): {result.stdout.decode()}")
        print(f"STDERR (mysql2): {result.stderr.decode()}")

        # Check for GTID error and handle it
        if "GTID state is not compatible" in result.stderr.decode():
            print("GTID compatibility issue detected. Trying to clean the GTID state before adding the instance.")
            # Here, you may want to reset GTID or handle the error.
            # You could issue a command to reset GTID sets (only if this is acceptable in your case)
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
                'cluster', 'add-instance', '--uri=inno@mysql2', '--recoveryMethod=increamental'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            time.sleep(120)
            print(f"STDOUT (mysql2 - retry): {result.stdout.decode()}")
            print(f"STDERR (mysql2 - retry): {result.stderr.decode()}")

        # Now, try adding the second instance (mysql3)
        result = subprocess.run([
            'docker', 'exec', 'mysql1',
            'mysqlsh', '-uinno', '-pinno', '--',
            'cluster', 'add-instance', '--uri=inno@mysql3', '--recoveryMethod=increamental'
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(120)
        print(f"STDOUT (mysql3): {result.stdout.decode()}")
        print(f"STDERR (mysql3): {result.stderr.decode()}")

        # Similarly, try adding the third instance (mysql4)
        result = subprocess.run([
            'docker', 'exec', 'mysql1',
            'mysqlsh', '-uinno', '-pinno', '--',
            'cluster', 'add-instance', '--uri=inno@mysql4', '--recoveryMethod=increamental'
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(120)
        print(f"STDOUT (mysql4): {result.stdout.decode()}")
        print(f"STDERR (mysql4): {result.stderr.decode()}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while adding instance: {e}")
        print(f"STDOUT: {e.stdout.decode() if e.stdout else 'No output'}")
        print(f"STDERR: {e.stderr.decode() if e.stderr else 'No error output'}")

@pytest.fixture(scope='module')
def host(setup_mysql_cluster):
    """ Simulates the `Router_Bootstrap` function """
    # Run mysql-router container
    docker_id = subprocess.check_output(
        ['docker', 'run', '-d', '--name', container_name_mysql_router, '--net', network_name,
         '-e', 'MYSQL_HOST=mysql1', '-e', 'MYSQL_PORT=3306', '-e', 'MYSQL_USER=inno',
         '-e', 'MYSQL_PASSWORD=inno', '-e', 'MYSQL_INNODB_CLUSTER_MEMBERS=4', router_docker_image]).decode().strip()
    subprocess.check_call(['docker','exec','--user','root',container_name_mysql_router,'microdnf','install','net-tools'])
    time.sleep(20)
    yield testinfra.get_host("docker://root@" + docker_id)
    subprocess.check_call(['docker', 'rm', '-f', docker_id])


#def test_data_add():
#    """ Simulates the `data_add` function """
#    # Start mysql-client container
#    command = [
#        'docker', 'run', '-d', '--name', 'mysql-client', '--hostname', 'mysql-client', '--net', network_name,
#        '-e', 'MYSQL_ROOT_PASSWORD=root', percona_docker_image
#    ]
#    docker_run(command)

    # Give time for the container to initialize
#    time.sleep(10)

    # Create sbtest user and schema
#    command = [
#        'docker', 'exec', '-it', 'mysql-client', 'mysql', '-h', 'mysql-router', '-P', '6446', '-uinno', '-pinno',
#        '-e', "CREATE SCHEMA sbtest; CREATE USER sbtest@'%' IDENTIFIED with mysql_native_password by  'password';",
#        '-e', "GRANT ALL PRIVILEGES ON sbtest.* to sbtest@'%';"
#    ]
#    docker_run(command)

    # Verify sbtest user
 #   command = [
 #       'docker', 'exec', '-it', 'mysql-client', 'mysql', '-h', 'mysql-router', '-P', '6447', '-uinno', '-pinno',
 #       '-e', "select host , user from mysql.user where user='sbtest';"
 #   ]
 #   docker_run(command)

    # Run sysbench for data insertion
 #   command = [
 #       'docker', 'run', '--rm', '--net', network_name, '--name', 'sb-prepare', 'severalnines/sysbench',
 #       'sysbench', '--db-driver=mysql', '--table-size=10000', '--tables=1', '--threads=1', '--mysql-host=mysql-router',
 #       '--mysql-port=6446', '--mysql-user=sbtest', '--mysql-password=password', '/usr/share/sysbench/oltp_insert.lua', 'prepare'
 #   ]
 #   docker_run(command)

    # Wait for the data to insert
 #   time.sleep(20)

    # Verify if the data has been inserted
 #   command = [
 #       'docker', 'exec', '-it', 'mysql-client', 'mysql', '-h', 'mysql-router', '-P', '6447', '-uinno', '-pinno',
 #       '-e', "SELECT count(*) from sbtest.sbtest1;"
 #   ]
 #   docker_run(command)

@pytest.fixture(scope='module')
def setup_mysql_cluster():
    """Setup MySQL cluster for router tests"""
    try:
        create_network()
        create_mysql_config()
        start_mysql_containers()
        create_new_user()
        verify_new_user()
        docker_restart()
        create_cluster()
        add_slave()
        yield
    finally:
        # Cleanup
        try:
            subprocess.run(['docker', 'rm', '-f', 'mysql1', 'mysql2', 'mysql3', 'mysql4', container_name_mysql_router], check=False)
            subprocess.run(['docker', 'network', 'rm', network_name], check=False)
        except Exception:
            pass

#test_data_add()

class TestRouterEnvironment:
    def test_mysqlrouter_version(self, host):
        command = "mysqlrouter --version"
        output = host.check_output(command)
        assert docker_tag in output

    def test_mysqlsh_version(self, host):
        command = "mysqlsh --version"
        output = host.check_output(command)
        assert ps_version in output

    def test_mysqlrouter_directory_permissions(self, host):
        assert host.file('/var/lib/mysqlrouter').user == 'mysql'
        assert host.file('/var/lib/mysqlrouter').group == 'mysql'
        assert oct(host.file('/var/lib/mysqlrouter').mode) == '0o755'

    def test_mysql_user(self, host):
        mysql_user = host.user('mysql')
        print(f"Username: {mysql_user.name}, UID: {mysql_user.uid}")
        assert mysql_user.exists
        assert mysql_user.uid == 1001

    def test_mysqlrouter_ports(self, host):
        host.socket("tcp://6446").is_listening
        host.socket("tcp://6447").is_listening
        host.socket("tcp://64460").is_listening
        host.socket("tcp://64470").is_listening

    def test_mysqlrouter_config(self, host):
        assert host.file("/etc/mysqlrouter/mysqlrouter.conf").exists
        assert host.file("/etc/mysqlrouter/mysqlrouter.conf").user == "root"
        assert host.file("/etc/mysqlrouter/mysqlrouter.conf").group == "root"
        assert oct(host.file("/etc/mysqlrouter/mysqlrouter.conf").mode) == "0o644"