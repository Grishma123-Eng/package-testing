# Test website links for PS.
# Expected version formats:
# PS_VER_FULL="8.0.34-26.1"
# PS_VER_FULL="5.7.44-48.1"

import os
import requests
import pytest
import json
import re
from packaging import version

PS_VER_FULL = os.environ.get("PS_VER_FULL")

# Verify format of passed PS_VER_FULL
assert PS_VER_FULL is not None, "Environment variable PS_VER_FULL must be set."
assert re.match(r'^\d+\.\d+\.\d+-\d+\.\d+$', PS_VER_FULL), \
    f"PS version format is not correct: {PS_VER_FULL}. Expected pattern: 8.0.34-26.1"

PS_VER = '.'.join(PS_VER_FULL.split('.')[:-1]) #8.0.34-26
PS_BUILD_NUM = PS_VER_FULL.split('.')[-1] # "1"


if version.parse(PS_VER) > version.parse("8.1.0"):
    DEB_SOFTWARE_FILES=['bullseye', 'bookworm', 'focal', 'jammy','noble']
    RHEL_SOFTWARE_FILES=['redhat/7', 'redhat/8', 'redhat/9']
elif version.parse(PS_VER) > version.parse("8.0.0") and version.parse(PS_VER) < version.parse("8.1.0"):
    DEB_SOFTWARE_FILES=['bullseye', 'bookworm', 'focal', 'jammy','noble']
    RHEL_SOFTWARE_FILES=['redhat/7', 'redhat/8', 'redhat/9']
elif version.parse(PS_VER) > version.parse("5.7.0") and version.parse(PS_VER) < version.parse("8.0.0"):
    DEB_SOFTWARE_FILES=['bullseye', 'bookworm', 'bionic', 'focal', 'jammy', 'noble']
    RHEL_SOFTWARE_FILES=['redhat/7', 'redhat/8', 'redhat/9']
else:
    raise AssertionError(f"Unsupported Percona Server version: {PS_VER}")

SOFTWARE_FILES=DEB_SOFTWARE_FILES+RHEL_SOFTWARE_FILES+['binary','source']
RHEL_EL={'redhat/7':'el7', 'redhat/8':'el8', 'redhat/9':'el9'}

def get_package_tuples():
    packages = []
    #base_path = f"https://downloads.percona.com/downloads/Percona-Server-{PS_VER}/Percona-Server-{PS_VER}-{PS_BUILD_NUM}"
    for software_file in SOFTWARE_FILES:
        data = 'version_files=Percona-Server-' + PS_VER + '|Percona-Server&software_files=' + software_file
        req = requests.post(
            "https://www.percona.com/products-api.php",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8"}
        )
        assert req.status_code == 200, f"Failed request for {software_file}: status {req.status_code}"
        assert req.text != '[]', f"No data returned for software file: {software_file}"
        # Test binary tarballs
        if software_file == 'binary':
            if version.parse(PS_VER) < version.parse("8.0.0"):
                glibc_versions=["2.17","2.35"]
            else:
                glibc_versions=["2.17","2.28","2.31","2.34","2.35"]

            for glibc_version in glibc_versions:
                assert f"Percona-Server-{PS_VER}-Linux.x86_64.glibc{glibc_version}-minimal.tar.gz" in req.text, f"Missing minimal tarball for glibc {glibc_version}"
                assert f"Percona-Server-{PS_VER}-Linux.x86_64.glibc{glibc_version}.tar.gz" in req.text, f"Missing tarball for glibc {glibc_version}"
                if glibc_version in ['2.34', '2.35'] and version.parse("8.0.0") < version.parse(PS_VER) < version.parse("8.1.0"):
                    assert f"Percona-Server-{PS_VER}-Linux.x86_64.glibc{glibc_version}-zenfs-minimal.tar.gz" in req.text
                    assert f"Percona-Server-{PS_VER}-Linux.x86_64.glibc{glibc_version}-zenfs.tar.gz" in req.text


        # Test source tarballs
        elif software_file == 'source':
            assert f"percona-server-{PS_VER}.tar.gz" in req.text, "Source tarball missing"
            assert (f"percona-server_{PS_VER}.orig.tar.gz" in req.text or
                    f"percona-server-5.7_{PS_VER}.orig.tar.gz" in req.text), "Source orig tarball missing"
            assert (f"percona-server-{PS_VER_FULL}.generic.src.rpm" in req.text or
                    f"Percona-Server-57-{PS_VER_FULL}.generic.src.rpm" in req.text), "Source RPM missing"
            
        else:
            if version.parse(PS_VER) >= version.parse("8.0.0"):
                if software_file in DEB_SOFTWARE_FILES:
                    ps_deb_name_suffix = f"{PS_VER}-{PS_BUILD_NUM}.{software_file}_amd64.deb"
                    deb_packages = [
                        "percona-server-server_",
                        "percona-server-test_",
                        "percona-server-client_",
                        "percona-server-rocksdb_",
                        "percona-mysql-router_",
                        "libperconaserverclient21-dev_",
                        "libperconaserverclient21_",
                        "percona-server-source_",
                        "percona-server-common_",
                        "percona-server-dbg_",
                    ]
                    assert any(
                        f"{pkg}{ps_deb_name_suffix}" in req.text for pkg in ["libperconaserverclient21-dev_", "libperconaserverclient22-dev_"]
                    ), "Missing libperconaserverclient-dev package"
                    assert any(
                        f"{pkg}{ps_deb_name_suffix}" in req.text for pkg in ["libperconaserverclient21_", "libperconaserverclient22_"]
                    ), "Missing libperconaserverclient package"

                    for pkg in deb_packages:
                        # Skip libperconaserverclientXX as checked above
                        if pkg.startswith("libperconaserverclient"):
                            continue
                        assert f"{pkg}{ps_deb_name_suffix}" in req.text, f"Missing package {pkg}{ps_deb_name_suffix}"
                if software_file in RHEL_SOFTWARE_FILES:
                    ps_rpm_name_suffix = f"{PS_VER}.{PS_BUILD_NUM}.{RHEL_EL[software_file]}.x86_64.rpm"
                    rpm_packages = [
                        "percona-server-server-",
                        "percona-server-test-",
                        "percona-server-client-",
                        "percona-server-rocksdb-",
                        "percona-mysql-router-",
                        "percona-server-devel-",
                        "percona-server-shared-",
                        "percona-icu-data-files-",
                        "percona-server-debuginfo-",
                    ]
                    for pkg in rpm_packages:
                        assert f"{pkg}{ps_rpm_name_suffix}" in req.text, f"Missing RPM package {pkg}{ps_rpm_name_suffix}"
                    if software_file != "redhat/9":
                        assert f"percona-server-shared-compat-{ps_rpm_name_suffix}" in req.text, "Missing shared-compat package"

            elif version.parse("5.7.0") <= ver_obj < version.parse("8.0.0"):
                if software_file in DEB_SOFTWARE_FILES:
                    ps_deb_name_suffix = f"{PS_VER}-{PS_BUILD_NUM}.{software_file}_amd64.deb"
                    deb_packages_57 = [
                        "percona-server-server-5.7_",
                        "percona-server-test-5.7_",
                        "percona-server-client-5.7_",
                        "percona-server-rocksdb-5.7_",
                        "percona-server-tokudb-5.7_",
                        "libperconaserverclient20-dev_",
                        "libperconaserverclient20_",
                        "percona-server-source-5.7_",
                        "percona-server-common-5.7_",
                        "percona-server-5.7-dbg_",
                    ]
                    for pkg in deb_packages_57:
                        assert f"{pkg}{ps_deb_name_suffix}" in req.text, f"Missing package {pkg}{ps_deb_name_suffix}"

                if software_file in RHEL_SOFTWARE_FILES:
                    ps_rpm_name_suffix = f"{PS_VER}.{PS_BUILD_NUM}.{RHEL_EL[software_file]}.x86_64.rpm"
                    rpm_packages_57 = [
                        "Percona-Server-server-57-",
                        "Percona-Server-test-57-",
                        "Percona-Server-client-57-",
                        "Percona-Server-rocksdb-57-",
                        "Percona-Server-tokudb-57-",
                        "Percona-Server-devel-57-",
                        "Percona-Server-shared-57-",
                        "Percona-Server-57-debuginfo-",
                    ]
                    for pkg in rpm_packages_57:
                        assert f"{pkg}{ps_rpm_name_suffix}" in req.text, f"Missing RPM package {pkg}{ps_rpm_name_suffix}"
                    if software_file != "redhat/9":
                        assert f"Percona-Server-shared-compat-57-{ps_rpm_name_suffix}" in req.text, "Missing shared-compat package"

        files = json.loads(req.text)
        for file in files:
            packages.append((software_file, file['filename'], file['link']))

    return packages

LIST_OF_PACKAGES = get_package_tuples()

# Check that every link from website is working (200 reply and has some content-length)
@pytest.mark.parametrize(('software_file', 'filename', 'link'), LIST_OF_PACKAGES)
def test_packages_site(software_file, filename, link):
    print(f'\nTesting {software_file}, file: {filename}')
    print(link)
    req = requests.head(link)
    assert req.status_code == 200, f"HEAD request failed for {link} with status {req.status_code}"
    content_length = int(req.headers.get('content-length', 0))
    assert content_length > 0, f"Content length is zero for {link}"
