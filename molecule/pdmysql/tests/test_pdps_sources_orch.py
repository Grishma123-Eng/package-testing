import pytest
from .settings import *
from packaging import version

VERSION = os.environ.get("VERSION")


@pytest.mark.orch_source
def test_integration(host):
    with host.sudo():
        dist = host.system_info.distribution
        if dist.lower() not in RHEL_DISTS and version.parse(VERSION) > version.parse("8.0.0") and version.parse(VERSION) < version.parse("8.1.0"):
            command = "mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root';\""
        elif dist.lower() not in RHEL_DISTS and version.parse(VERSION) >= version.parse("8.1.0"):
            command = "mysql -e \"ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'root';\""
            result = host.run(command)
            assert result.rc == 0, (result.stderr, result.stdout)
        test_cmd = "cd /root/orchestrator/ && ./tests/integration/test.sh mysql"
        test = host.run(test_cmd)
        print(test.stdout)
        print(test.stderr)
        assert test.rc == 0
