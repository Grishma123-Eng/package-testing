#!/usr/bin/env bash
export PATH=${HOME}/.local/bin:${PATH}

# OS detection
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS_ID=$ID
  OS_VERSION=$VERSION_ID
else
  OS_ID="unknown"
  OS_VERSION="unknown"
fi

PXC_MAJOR_VERSION="$(echo ${PXC_VERSION}|cut -d'.' -f1,2)"

echo "Installing dependencies..."

if [ "$OS_ID" = "amzn" ] && [[ "$OS_VERSION" == 2023* ]]; then
  echo "Detected Amazon Linux 2023"
  sudo dnf install -y python3 python3-pip git curl wget tar gzip which findutils glibc-langpack-en libaio numactl openssl socat lsof libev

  pip3 install --user pytest-testinfra pytest

  if [ "${PXC_MAJOR_VERSION}" = "5.7" ]; then
    sudo dnf install -y https://repo.percona.com/yum/percona-release-latest.noarch.rpm
    sudo percona-release enable pxb-24 testing
    sudo dnf install -y percona-xtrabackup-24
  fi

elif [ -f /etc/redhat-release ]; then
  sudo yum install -y libaio numactl openssl socat lsof
  sudo yum install -y perl-Data-Dumper

  if grep -q "release 6" /etc/redhat-release; then
    sudo ../../centos6.sh
    sudo yum install -y rh-python36 rh-python36-python-pip
    source /opt/rh/rh-python36/enable
  else
    sudo yum install -y python3 python3-pip
  fi

  sudo yum install -y libev

  if [ "${PXC_MAJOR_VERSION}" = "5.7" ]; then
    sudo yum install -y https://repo.percona.com/yum/percona-release-latest.noarch.rpm
    sudo percona-release enable pxb-24 testing
    sudo yum install -y percona-xtrabackup-24
  fi

else
  if ! command -v apt-get >/dev/null; then
    echo "Error: apt-get not found and OS is not supported."
    exit 1
  fi

  sudo apt-get -qq update
  UCF_FORCE_CONFOLD=1 DEBIAN_FRONTEND=noninteractive sudo -E apt-get -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -qq -y install openssl

  if [[ $(lsb_release -sc) == 'xenial' ]]; then
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt -y install python3.6
    sudo rm /usr/bin/python3 && sudo ln -sf /usr/bin/python3.6 /usr/bin/python3
    wget -O get-pip.py "https://bootstrap.pypa.io/get-pip.py" && sudo python3 get-pip.py
    sudo apt install -y libcurl4-openssl-dev
  else
    sudo apt install -y python3 python3-pip
  fi

  sudo apt install -y python3 python3-pip libaio1 libnuma1 socat lsof curl libev4

  if [ "${PXC_MAJOR_VERSION}" = "5.7" ]; then
    wget -q https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb
    sudo dpkg -i percona-release_latest.$(lsb_release -sc)_all.deb
    sudo percona-release enable pxb-24 testing
    sudo apt update
    sudo apt-get install -y percona-xtrabackup-24
  fi
fi

# Always install Python test tools (with exception for Bookworm)
if [[ $(command -v lsb_release >/dev/null && lsb_release -sc) == 'bookworm' ]]; then
  pip3 install --user --break-system-packages pytest-testinfra pytest
else
  pip3 install --user pytest-testinfra pytest
fi

# Rest of your script remains unchanged
TARBALL_NAME=$(basename "$(find . -maxdepth 1 -name '*.tar.gz'|head -n1)")
if [ -z "${TARBALL_NAME}" ]; then
  echo "Please put PXC tarball into this directory!"
  exit 1
fi
if [ -z "${PXC_VERSION}" ]; then
  echo "PXC_VERSION environment variable needs to be set!"
  echo "export PXC_VERSION=\"8.0.17-8\""
fi
if [ -z "${PXC_REVISION}" ]; then
  echo "PXC_REVISION environment variable needs to be set!"
  echo "export PXC_REVISION=\"868a4ef\""
fi
if [ -z "${WSREP_VERSION}" ]; then
  echo "WSREP_VERSION environment variable needs to be set!"
  echo "export WSREP_VERSION=\"26.4.3\""
fi
if [ -z "${PXC57_PKG_VERSION}" ]; then
  echo "PXC57_PKG_VERSION environment variable needs to be set!"
  echo "export PXC57_PKG_VERSION=\"5.7.31-rel34-43.2\""
fi
tar xf "${TARBALL_NAME}"
PXC_DIR_NAME=$(echo "${TARBALL_NAME}"|sed 's/.tar.gz$//'|sed 's/.deb$//'|sed 's/.rpm$//')
export BASE_DIR="${PWD}/${PXC_DIR_NAME}"
cp conf/*cnf $BASE_DIR/

PRO=$(echo ${PRO})

echo "Running tests..."
echo "Pro value inside run.sh is ${PRO}"
echo "${PXC_DIR_NAME}"
python3 -m pytest --ignore="${PXC_DIR_NAME}"/percona-xtradb-cluster-tests -v --junit-xml report.xml $@