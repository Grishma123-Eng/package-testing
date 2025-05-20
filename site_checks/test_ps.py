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
assert re.search(r'^\d+\.\d+\.\d+-\d+\.\d+$', PS_VER_FULL), "PS version format is not correct. Expected pattern with build: 8.0.34-26.1"

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

SOFTWARE_FILES=DEB_SOFTWARE_FILES+RHEL_SOFTWARE_FILES+['binary','source']
RHEL_EL={'redhat/7':'el7', 'redhat/8':'el8', 'redhat/9':'el9'}

def url_exists(url):
    resp = requests.head(url)
    return resp.status_code == 200 and int(resp.headers.get('content-length', 0)) > 0


def get_package_tuples():
    list = []
    base_path = f"https://downloads.percona.com/downloads/Percona-Server-{PS_VER}/Percona-Server-{PS_VER}-{PS_BUILD_NUM}"
    for software_file in SOFTWARE_FILES:
    #    data = 'version_files=Percona-Server-' + PS_VER + '|Percona-Server&software_files=' + software_file
     #   req = requests.post("https://www.percona.com/products-api.php",data=data,headers = {"content-type": "application/x-www-form-urlencoded; charset=UTF-8"})
      #  assert req.status_code == 200
      #  assert req.text != '[]', software_file
        # Test binary tarballs
        if software_file == 'binary':
            if version.parse(PS_VER) < version.parse("8.0.0"):
                glibc_versions=["2.17","2.35"]
            else:
                glibc_versions=["2.17","2.28","2.31","2.34","2.35"]
            for glibc_version in glibc_versions:
                for suffix in ["", "-minimal", "-zenfs", "-zenfs-minimal"]:
                    filename = f"Percona-Server-{PS_VER}-Linux.x86_64.glibc{glibc_version}{suffix}.tar.gz"
                    url = f"{base_path}/binary/tarball/{filename}"
                    if url_exists(url):
                        list.append(("binary", filename, url))
               # assert "Percona-Server-" + PS_VER + "-Linux.x86_64.glibc"+glibc_version+"-minimal.tar.gz" in req.text
               # assert "Percona-Server-" + PS_VER + "-Linux.x86_64.glibc"+glibc_version+".tar.gz" in req.text
               # if glibc_version in ['2.34', '2.35'] and version.parse(PS_VER) > version.parse("8.0.0") and version.parse(PS_VER) < version.parse("8.1.0"):
               #     assert "Percona-Server-" + PS_VER + "-Linux.x86_64.glibc"+glibc_version+"-zenfs-minimal.tar.gz" in req.text
               #     assert "Percona-Server-" + PS_VER + "-Linux.x86_64.glibc"+glibc_version+"-zenfs.tar.gz" in req.text
        # Test source tarballs
        elif software_file == 'source':
            candidates = [
                f"percona-server-{PS_VER}.tar.gz",
                f"percona-server_{PS_VER}.orig.tar.gz",
                f"percona-server-5.7_{PS_VER}.orig.tar.gz",
                f"percona-server-{PS_VER_FULL}.generic.src.rpm",
                f"Percona-Server-57-{PS_VER_FULL}.generic.src.rpm"
            ]
            for fname in candidates:
                url = f"{base_path}/source/tarball/{fname}"
                if url_exists(url):
                    list.append(("source", fname, url))
           # print(f"Loop 2 {software_file}")
            #assert "percona-server-" + PS_VER + ".tar.gz" in req.text
            #assert "percona-server_" + PS_VER  + ".orig.tar.gz" in req.text or "percona-server-5.7_" + PS_VER  + ".orig.tar.gz" in req.text
            #assert "percona-server-" + PS_VER_FULL  + ".generic.src.rpm" in req.text or "Percona-Server-57-" + PS_VER_FULL + ".generic.src.rpm" in req.text
        # Test packages for every OS
        else:
            if version.parse(PS_VER) > version.parse("8.0.0"):
                if software_file in DEB_SOFTWARE_FILES:
                    ps_deb_suffix = f"{PS_VER}-{PS_BUILD_NUM}.{software_file}_amd64.deb"
            deb_filenames = [
                f"percona-server-server_{ps_deb_suffix}",
                f"percona-server-test_{ps_deb_suffix}",
                f"percona-server-client_{ps_deb_suffix}",
                f"percona-server-rocksdb_{ps_deb_suffix}",
                f"percona-mysql-router_{ps_deb_suffix}",
                f"libperconaserverclient21-dev_{ps_deb_suffix}",
                f"libperconaserverclient21_{ps_deb_suffix}",
                f"libperconaserverclient22-dev_{ps_deb_suffix}",
                f"libperconaserverclient22_{ps_deb_suffix}",
                f"percona-server-source_{ps_deb_suffix}",
                f"percona-server-common_{ps_deb_suffix}",
                f"percona-server-dbg_{ps_deb_suffix}"
            ]
            for fname in deb_filenames:
                url = f"{base_path}/binary/debian/{software_file}/x86_64/{fname}"
                if url_exists(url):
                    list.append((software_file, fname, url))
                 #   ps_deb_name_suffix=PS_VER + "-" + PS_BUILD_NUM + "." + software_file + "_amd64.deb"
                 #   assert "percona-server-server_" + ps_deb_name_suffix in req.text
                 #   assert "percona-server-test_" + ps_deb_name_suffix in req.text
                 #   assert "percona-server-client_" + ps_deb_name_suffix in req.text
                 #   assert "percona-server-rocksdb_" + ps_deb_name_suffix in req.text
                 #   assert "percona-mysql-router_" + ps_deb_name_suffix in req.text
                 #   assert "libperconaserverclient21-dev_" + ps_deb_name_suffix in req.text or "libperconaserverclient22-dev_" + ps_deb_name_suffix in req.text
                 #   assert "libperconaserverclient21_" + ps_deb_name_suffix in req.text or "libperconaserverclient22_" + ps_deb_name_suffix in req.text
                 #   assert "percona-server-source_" + ps_deb_name_suffix in req.text
                 #   assert "percona-server-common_" + ps_deb_name_suffix in req.text
                 #   assert "percona-server-dbg_" + ps_deb_name_suffix in req.text
                if software_file in RHEL_SOFTWARE_FILES:
                    ps_rpm_suffix = f"{PS_VER}.{PS_BUILD_NUM}.{RHEL_EL[software_file]}.x86_64.rpm"
            rpm_filenames = [
                f"percona-server-server-{ps_rpm_suffix}",
                f"percona-server-test-{ps_rpm_suffix}",
                f"percona-server-client-{ps_rpm_suffix}",
                f"percona-server-rocksdb-{ps_rpm_suffix}",
                f"percona-mysql-router-{ps_rpm_suffix}",
                f"percona-server-devel-{ps_rpm_suffix}",
                f"percona-server-shared-{ps_rpm_suffix}",
                f"percona-icu-data-files-{ps_rpm_suffix}",
                f"percona-server-debuginfo-{ps_rpm_suffix}"
            ]
            if software_file != "redhat/9":
                rpm_filenames.append(f"percona-server-shared-compat-{ps_rpm_suffix}")

            for fname in rpm_filenames:
                url = f"{base_path}/binary/redhat/{software_file.split('/')[-1]}/x86_64/{fname}"
                if url_exists(url):
                    list.append((software_file, fname, url))
    return list
                #    ps_rpm_name_suffix=PS_VER + "." + PS_BUILD_NUM + "." + RHEL_EL[software_file] + ".x86_64.rpm"
                 #   assert "percona-server-server-" + ps_rpm_name_suffix in req.text
                  #  assert "percona-server-test-" + ps_rpm_name_suffix in req.text
                  #  assert "percona-server-client-" + ps_rpm_name_suffix in req.text
                  ##  assert "percona-server-rocksdb-" + ps_rpm_name_suffix in req.text
                  # assert "percona-mysql-router-" + ps_rpm_name_suffix in req.text
                  #  assert "percona-server-devel-" + ps_rpm_name_suffix in req.text
                  #  assert "percona-server-shared-" + ps_rpm_name_suffix in req.text
                  #  assert "percona-icu-data-files-" + ps_rpm_name_suffix in req.text
                  #  if software_file != "redhat/9":
                   #     assert "percona-server-shared-compat-" + ps_rpm_name_suffix in req.text
                    #assert "percona-server-debuginfo-" + ps_rpm_name_suffix in req.text
    
#####

LIST_OF_PACKAGES = get_package_tuples()

# Check that every link from website is working (200 reply and has some content-length)
@pytest.mark.parametrize(('software_file','filename','link'),LIST_OF_PACKAGES)
def test_packages_site(software_file,filename,link):
    print('\nTesting ' + software_file + ', file: ' + filename)
    print(link)
    req = requests.head(link)
    if not re.search(r'Percona-Server.*\.diff\.gz', link):
        assert req.status_code == 200 and int(req.headers['content-length']) > 0, link
   # assert req.status_code == 200 and int(req.headers['content-length']) > 0, link
