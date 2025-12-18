#!/usr/bin/env python3
import subprocess
import re
import os
import shlex
import time
import uuid

class MySQL:
    def __init__(self, base_dir, features=None, host=None):
        if features is None:
            features = []

        self.basedir = base_dir
        self.features = features
        self.host = host

        self.port = "3306"

        # Unique runtime paths (avoid CI collisions)
        uid = str(uuid.uuid4())[:8]
        self.datadir = f"/tmp/mysql-data-{uid}"
        self.socket = f"/tmp/mysql-{uid}.sock"
        self.pidfile = f"/tmp/mysql-{uid}.pid"

        self.logfile = f"{self.basedir}/log/master.err"

        self.mysql = f"{self.basedir}/bin/mysql"
        self.mysqld = f"{self.basedir}/bin/mysqld"
        self.mysqladmin = f"{self.basedir}/bin/mysqladmin"
        self.mysql_install_db = f"{self.basedir}/scripts/mysql_install_db"

        self.run_user = os.getenv("MYSQL_RUN_USER", "mysql")

        # --------------------------------------------------
        # FIPS ENVIRONMENT (CRITICAL for OL9 / OpenSSL 3)
        # --------------------------------------------------
        if "fips" in self.features:
            os.environ.setdefault("OPENSSL_MODULES", "/usr/lib64/ossl-modules")
            os.environ.setdefault("OPENSSL_CONF", "/etc/ssl/openssl.cnf")

        # --------------------------------------------------
        # Validate binaries
        # --------------------------------------------------
        if self.host:
            if not self.host.file(self.basedir).exists:
                raise FileNotFoundError(f"Base directory not found: {self.basedir}")
            if not self.host.file(self.mysqld).exists:
                raise FileNotFoundError(f"mysqld not found: {self.mysqld}")
            version_output = self.host.check_output(f"{self.mysqld} --version")
        else:
            if not os.path.exists(self.mysqld):
                raise FileNotFoundError(f"mysqld not found: {self.mysqld}")
            version_output = subprocess.check_output(
                [self.mysqld, "--version"], universal_newlines=True
            )

        m = re.search(r"[0-9]+\.[0-9]+", version_output)
        self.major_version = m.group()

        # --------------------------------------------------
        # Engine admin binary
        # --------------------------------------------------
        if self.major_version == "5.6":
            self.psadmin = f"{self.basedir}/bin/ps_tokudb_admin"
        else:
            self.psadmin = f"{self.basedir}/bin/ps-admin"

        # --------------------------------------------------
        # Initialize datadir
        # --------------------------------------------------
        if self.host:
            self.host.run(f"rm -rf {self.datadir}")
            self.host.run(f"mkdir -p {self.datadir} {self.basedir}/log")
        else:
            subprocess.call(["rm", "-rf", self.datadir])
            os.makedirs(self.datadir, exist_ok=True)
            os.makedirs(f"{self.basedir}/log", exist_ok=True)

        if self.major_version == "5.6":
            init_cmd = f"{self.mysql_install_db} --no-defaults --basedir={self.basedir} --datadir={self.datadir}"
        else:
            init_cmd = f"{self.mysqld} --no-defaults --initialize-insecure --basedir={self.basedir} --datadir={self.datadir}"

        if self.host:
            self.host.check_output(init_cmd)
        else:
            subprocess.check_call(init_cmd.split())

        # --------------------------------------------------
        # FIPS PRE-FLIGHT CHECK
        # --------------------------------------------------
        self.extra_param = []

        if "fips" in self.features:
            if not self._fips_preflight():
                raise RuntimeError(
                    "FIPS requested but OS crypto is NOT in FIPS mode "
                    "(/proc/sys/crypto/fips_enabled != 1)"
                )

            self.extra_param = [
                "--ssl-fips-mode=ON",
                "--log-error-verbosity=3",
            ]


    # ------------------------------------------------------
    # FIPS PRECHECK
    # ------------------------------------------------------
    def _fips_preflight(self):
    """
    Returns True ONLY if the OS crypto layer is in FIPS mode.
    """
    try:
        if self.host:
            val = self.host.check_output(
                "cat /proc/sys/crypto/fips_enabled"
            ).strip()
        else:
            with open("/proc/sys/crypto/fips_enabled") as f:
                val = f.read().strip()

        return val == "1"
    except Exception:
        return False

    # ------------------------------------------------------
    # START MYSQL
    # ------------------------------------------------------
    def start(self):
        params = [
            "--no-defaults",
            f"--basedir={self.basedir}",
            f"--datadir={self.datadir}",
            f"--socket={self.socket}",
            f"--port={self.port}",
            f"--pid-file={self.pidfile}",
            f"--log-error={self.logfile}",
            "--server-id=1",
            f"--user={self.run_user}",
        ] + self.extra_param

        cmd = " ".join([self.mysqld] + params)

        if self.host:
            self.host.run(f"id {self.run_user} || useradd -r -s /sbin/nologin {self.run_user}")
            self.host.run(f"chown -R {self.run_user}:{self.run_user} {self.datadir} {self.basedir}")
            self.host.run(f"nohup {cmd} > /tmp/mysqld-start.log 2>&1 &")
        else:
            subprocess.Popen(cmd.split(), env=os.environ)

        # Wait for socket
        for _ in range(30):
            time.sleep(1)
            if self._socket_exists():
                try:
                    self._ping()
                    return
                except Exception:
                    continue

        self._fail_startup()

    def _socket_exists(self):
        if self.host:
            return self.host.file(self.socket).exists
        return os.path.exists(self.socket)

    def _ping(self):
        if self.host:
            self.host.check_output(f"{self.mysqladmin} -uroot -S{self.socket} ping")
        else:
            subprocess.check_call(
                [self.mysqladmin, "-uroot", f"-S{self.socket}", "ping"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def _fail_startup(self):
        if self.host and self.host.file("/tmp/mysqld-start.log").exists:
            raise RuntimeError(
                "MySQL failed to start:\n"
                + self.host.file("/tmp/mysqld-start.log").content_string
            )
        raise RuntimeError("MySQL failed to start and no logs were produced")

    # ------------------------------------------------------
    # STOP / CLEANUP
    # ------------------------------------------------------
    def stop(self):
        try:
            if self.host:
                self.host.check_output(f"{self.mysqladmin} -uroot -S{self.socket} shutdown")
            else:
                subprocess.check_call([self.mysqladmin, "-uroot", f"-S{self.socket}", "shutdown"])
        except Exception:
            pass

    def purge(self):
        self.stop()
        if self.host:
            self.host.run(f"rm -rf {self.datadir}")
        else:
            subprocess.call(["rm", "-rf", self.datadir])

    # ------------------------------------------------------
    # QUERY HELPERS
    # ------------------------------------------------------
    def run_query(self, query):
        cmd = f"{self.mysql} -uroot -S{self.socket} -s -N -e {shlex.quote(query)}"
        if self.host:
            return self.host.check_output(cmd)
        return subprocess.check_output(cmd, shell=True, universal_newlines=True)

    def install_function(self, fname, soname, return_type):
        self.run_query(f'CREATE FUNCTION {fname} RETURNS {return_type} SONAME "{soname}";')

    def install_plugin(self, pname, soname):
        self.run_query(f'INSTALL PLUGIN {pname} SONAME "{soname}";')

    def install_component(self, cname):
        self.run_query(f'INSTALL COMPONENT "file://{cname}";')

    def check_engine_active(self, engine):
        out = self.run_query(
            f'SELECT SUPPORT FROM information_schema.ENGINES WHERE ENGINE="{engine}";'
        )
        return "YES" in out
