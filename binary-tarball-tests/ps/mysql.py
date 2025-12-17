#!/usr/bin/env python3
import subprocess
import re
import os
import shlex
import time

class MySQL:
    def __init__(self, base_dir, features=[], host=None):
        self.basedir = base_dir
        self.port = '3306'
        self.datadir = base_dir+'/data'
        self.socket = '/tmp/mysql.sock'
        self.logfile = base_dir+'/log/master.err'
        self.mysql = base_dir+'/bin/mysql'
        self.mysqld = base_dir+'/bin/mysqld'
        self.mysqladmin = base_dir+'/bin/mysqladmin'
        self.pidfile = base_dir+'/mysql.pid'
        self.mysql_install_db = base_dir+'/scripts/mysql_install_db'
        self.features=features
        self.host = host  # Store host object for testinfra access
        self.run_user = os.getenv("MYSQL_RUN_USER", "mysql")

        if 'fips' in self.features:
            self.extra_param=['--ssl-fips-mode=ON', '--log-error-verbosity=3']
        else:
            self.extra_param=[]

        # Use host  object if available (testinfra), otherwise fall back to subprocess
        if self.host:
            # Use testinfra host (runs via Ansible, can access root files)
            if not self.host.file(self.basedir).exists:
                raise FileNotFoundError(f"Base directory does not exist: {self.basedir}")
            if not self.host.file(self.mysqld).exists:
                raise FileNotFoundError(f"mysqld binary does not exist: {self.mysqld}")
            
            self.host.run(f'rm -Rf {self.datadir}')
            self.host.run(f'rm -f {self.logfile}')
            if not self.host.file(self.basedir+'/log').exists:
                self.host.run(f'mkdir -p {self.basedir}/log')
            
            output = self.host.check_output(f'{self.mysqld} --version')
        else:
            # Original subprocess code (for backward compatibility)
            if not os.path.exists(self.basedir):
                raise FileNotFoundError(f"Base directory does not exist: {self.basedir}")
            if not os.path.exists(self.mysqld):
                raise FileNotFoundError(f"mysqld binary does not exist: {self.mysqld}")
            if not os.access(self.mysqld, os.X_OK):
                raise PermissionError(f"mysqld binary is not executable: {self.mysqld}")

            subprocess.call(['rm','-Rf',self.datadir])
            subprocess.call(['rm','-f',self.logfile])
            if not os.path.exists(self.basedir+'/log'):
                subprocess.call(['mkdir','-p',self.basedir+'/log'])
            output = subprocess.check_output([self.mysqld, '--version'],universal_newlines=True)
        
        x = re.search(r"[0-9]+\.[0-9]+", output)
        self.major_version = x.group()
        
        if self.major_version == "5.6":
            os.environ['LD_PRELOAD'] = self.basedir+'/lib/mysql/libjemalloc.so.1 '+self.basedir+'/lib/libHotBackup.so'
            self.psadmin = base_dir+'/bin/ps_tokudb_admin'
            if self.host:
                self.host.check_output(f'{self.mysql_install_db} --no-defaults --basedir={self.basedir} --datadir={self.datadir}')
            else:
                subprocess.check_call([self.mysql_install_db, '--no-defaults', '--basedir='+self.basedir,'--datadir='+self.datadir])
        elif self.major_version == "5.7":
            os.environ['LD_PRELOAD'] = self.basedir+'/lib/mysql/libjemalloc.so.1 '+self.basedir+'/lib/libHotBackup.so'
            self.psadmin = base_dir+'/bin/ps-admin'
            if self.host:
                self.host.check_output(f'{self.mysqld} --no-defaults --initialize-insecure --basedir={self.basedir} --datadir={self.datadir}')
            else:
                subprocess.check_call([self.mysqld, '--no-defaults', '--initialize-insecure','--basedir='+self.basedir,'--datadir='+self.datadir])
        else:
            os.environ['LD_PRELOAD'] = self.basedir+'/lib/mysql/libjemalloc.so.1'
            self.psadmin = base_dir+'/bin/ps-admin'
            if self.host:
                 self.host.check_output(f'{self.mysqld} --no-defaults --initialize-insecure --basedir={self.basedir} --datadir={self.datadir}')
            else:
                subprocess.check_call([self.mysqld, '--no-defaults', '--initialize-insecure','--basedir='+self.basedir,'--datadir='+self.datadir])

    def start(self):
        self.basic_param=['--no-defaults','--basedir='+self.basedir,'--datadir='+self.datadir,'--tmpdir='+self.datadir,'--socket='+self.socket,'--port='+self.port,'--log-error='+self.logfile,'--pid-file='+self.pidfile,'--server-id=1']
        if self.run_user:
            self.basic_param.append(f'--user={self.run_user}')
        if self.host:
            # Ensure run user exists and owns the base dir
            self.host.run(f'id {self.run_user} || useradd -r -s /sbin/nologin {self.run_user}')
            self.host.run(f'chown -R {self.run_user}:{self.run_user} {self.basedir}')
            # Use host.run() for background process with nohup to keep it alive
            cmd = ' '.join([self.mysqld] + self.basic_param + self.extra_param)
            # Use nohup and redirect output to keep process alive
            self.host.run(f'nohup {cmd} > {self.logfile} 2>&1 &')
            # Wait for socket to be created (max 30 seconds)
            max_wait = 30
            wait_time = 0
            while wait_time < max_wait:
                self.host.run('sleep 1')
                wait_time += 1
                if self.host.file(self.socket).exists:
                    # Socket exists, wait a bit more for MySQL to be ready
                    self.host.run('sleep 2')
                    # Try to connect to verify MySQL is ready
                    try:
                        self.host.check_output(f'{self.mysqladmin} -uroot -S{self.socket} ping')
                        break
                    except:
                        continue
            if not self.host.file(self.socket).exists:
                # Check error log for issues
                if self.host.file(self.logfile).exists:
                    error_log = self.host.file(self.logfile).content_string
                    raise RuntimeError(f"MySQL failed to start. Error log:\n{error_log}")
                else:
                    raise RuntimeError("MySQL failed to start and no error log found")
        else:
            subprocess.Popen([self.mysqld]+ self.basic_param + self.extra_param, env=os.environ)
            # Wait for socket to be created
            max_wait = 30
            wait_time = 0
            while wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
                if os.path.exists(self.socket):
                    time.sleep(2)
                    # Try to connect to verify MySQL is ready
                    try:
                        subprocess.check_call([self.mysqladmin,'-uroot','-S'+self.socket,'ping'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        break
                    except:
                        continue
            if not os.path.exists(self.socket):
                if os.path.exists(self.logfile):
                    with open(self.logfile, 'r') as f:
                        error_log = f.read()
                    raise RuntimeError(f"MySQL failed to start. Error log:\n{error_log}")
                else:
                    raise RuntimeError("MySQL failed to start and no error log found")

    def stop(self):
        if self.host:
            self.host.check_output(f'{self.mysqladmin} -uroot -S{self.socket} shutdown')
            self.host.run('sleep 5')
        else:
            subprocess.check_call([self.mysqladmin,'-uroot','-S'+self.socket,'shutdown'])
            subprocess.call(['sleep','5'])

    def restart(self):
        self.stop()
        self.start()

    def purge(self):
        self.stop()
        if self.host:
            self.host.run(f'rm -Rf {self.datadir}')
            self.host.run(f'rm -f {self.logfile}')
        else:
            subprocess.call(['rm','-Rf',self.datadir])
            subprocess.call(['rm','-f',self.logfile])

    def run_query(self,query):
        command = self.mysql+' --user=root -S'+self.socket+' -s -N -e '+shlex.quote(query)
        if self.host:
            return self.host.check_output(command)
        else:
            return subprocess.check_output(command,shell=True,universal_newlines=True)

    def install_function(self, fname, soname, return_type):
        query = 'CREATE FUNCTION {} RETURNS {} SONAME "{}";'.format(fname,return_type,soname)
        self.run_query(query)
        query = 'SELECT name FROM mysql.func WHERE dl = "{}";'.format(soname)
        output = self.run_query(query)
        assert fname in output

    def install_plugin(self, pname, soname):
        query = 'INSTALL PLUGIN {} SONAME "{}";'.format(pname,soname)
        self.run_query(query)
        query = 'SELECT plugin_status FROM information_schema.plugins WHERE plugin_name = "{}";'.format(pname)
        output = self.run_query(query)
        assert 'ACTIVE' in output

    def install_component(self, cname):
        query = 'INSTALL COMPONENT "file://{}";'.format(cname)
        self.run_query(query)
        query = 'SELECT component_urn FROM mysql.component where component_urn like "%{}%";'.format(cname)
        output = self.run_query(query)
        assert cname in output

    def check_engine_active(self, engine):
        query = 'select SUPPORT from information_schema.ENGINES where ENGINE = "{}";'.format(engine)
        output = self.run_query(query)
        if 'YES' in output:
            return True
        else:
            return False