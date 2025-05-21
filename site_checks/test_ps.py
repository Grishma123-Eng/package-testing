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
        data = 'version_files=percona-Server-' + PS_VER + '&software_files=' + software_file
        req = requests.post(
            "https://www.percona.com/products-api.php",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8"}
        )
        assert req.status_code == 200, f"Failed request for {software_file}: status {req.status_code}"
        assert req.text != '[]', f"No data returned for software file: {software_file}"

        if "percona-server" not in req.text:
            print(f"Skipping {software_file}: no percona-server content in API response.")
            continue
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
                    assert f"percona-server-server_{ps_deb_name_suffix}" in req.text
                    assert f"percona-server-test_{ps_deb_name_suffix}" in req.text
                    assert f"percona-server-client_{ps_deb_name_suffix}" in req.text
                    assert f"percona-server-rocksdb_{ps_deb_name_suffix}" in req.text
                    assert f"percona-mysql-router_{ps_deb_name_suffix}" in req.text
                    assert any(x in req.text for x in [
                        f"libperconaserverclient21-dev_{ps_deb_name_suffix}",
                        f"libperconaserverclient22-dev_{ps_deb_name_suffix}"
                    ]), "Missing libperconaserverclient-dev package"
                    assert any(x in req.text for x in [
                        f"libperconaserverclient21_{ps_deb_name_suffix}",
                        f"libperconaserverclient22_{ps_deb_name_suffix}"
                    ]), "Missing libperconaserverclient package"
                    assert f"percona-server-source_{ps_deb_name_suffix}" in req.text
                    assert f"percona-server-common_{ps_deb_name_suffix}" in req.text
                    assert f"percona-server-dbg_{ps_deb_name_suffix}" in req.text
                    
                elif software_file in RHEL_SOFTWARE_FILES:
                    ps_rpm_name_suffix = f"{PS_VER}.{PS_BUILD_NUM}.{RHEL_EL[software_file]}.x86_64.rpm"
                    assert f"percona-server-server-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-server-test-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-server-client-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-server-rocksdb-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-mysql-router-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-server-devel-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-server-shared-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-icu-data-files-{ps_rpm_name_suffix}" in req.text
                    if software_file != "redhat/9":
                        assert f"percona-server-shared-compat-{ps_rpm_name_suffix}" in req.text
                    assert f"percona-server-debuginfo-{ps_rpm_name_suffix}" in req.text

                elif version.parse("5.7.0") < version.parse(PS_VER) < version.parse("8.0.0"):
                    if software_file in DEB_SOFTWARE_FILES:
                        ps_deb_name_suffix = PS_VER + "-" + PS_BUILD_NUM + "." + software_file + "_amd64.deb"
                        assert f"percona-server-server-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-test-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-client-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-rocksdb-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-tokudb-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"libperconaserverclient20-dev_{ps_deb_name_suffix}" in req.text
                        assert f"libperconaserverclient20_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-source-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-common-5.7_{ps_deb_name_suffix}" in req.text
                        assert f"percona-server-5.7-dbg_{ps_deb_name_suffix}" in req.text
                elif software_file in RHEL_SOFTWARE_FILES:
                    ps_rpm_name_suffix = PS_VER + "." + PS_BUILD_NUM + "." + RHEL_EL[software_file] + ".x86_64.rpm"
                    assert f"Percona-Server-server-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-test-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-client-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-rocksdb-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-tokudb-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-devel-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-shared-57-{ps_rpm_name_suffix}" in req.text
                    if software_file != "redhat/9":
                        assert f"Percona-Server-shared-compat-57-{ps_rpm_name_suffix}" in req.text
                    assert f"Percona-Server-57-debuginfo-{ps_rpm_name_suffix}" in req.text

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
