#!/usr/bin/env bash
set -euo pipefail  # Stop on first error, treat unset variables as errors

export PATH=${HOME}/.local/bin:${PATH}

# Ensure PXC_VERSION is set before using it
if [[ -z "${PXC_VERSION:-}" ]]; then
  echo "ERROR: PXC_VERSION environment variable is not set!"
  echo "ℹ️  Example: export PXC_VERSION=\"8.0.17-8\""
  exit 1
fi

PXC_MAJOR_VERSION="$(echo ${PXC_VERSION} | cut -d'.' -f1,2)"

echo "Installing dependencies..."
if [[ -f /etc/redhat-release ]]; then
  sudo yum install -y libaio numactl openssl socat lsof libev perl-Data-Dumper

  if grep -q "release 6" /etc/redhat-release; then
    sudo ../../centos6.sh
    sudo yum install -y rh-python36 rh-python36-python-pip
    source /opt/rh/rh-python36/enable
  else
    sudo yum install -y python3 python3-pip
  fi

  if [[ "${PXC_MAJOR_VERSION}" == "5.7" ]]; then
    sudo yum install -y https://repo.percona.com/yum/percona-release-latest.noarch.rpm
    sudo percona-release enable pxb-24 testing
    sudo yum install -y percona-xtrabackup-24
  fi
else
  sudo apt update -y
  sudo apt install -y lsb-release || (echo " ERROR: lsb-release package is missing!" && exit 1)
  sudo apt install -y python3 python3-pip libaio1 libnuma1 socat lsof curl libev4

  if [[ "$(lsb_release -sc)" == "xenial" ]]; then
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update -y
    sudo apt install -y python3.6
    sudo ln -sf /usr/bin/python3.6 /usr/bin/python3
    wget -O get-pip.py "https://bootstrap.pypa.io/get-pip.py" && sudo python3 get-pip.py
  fi
  if [[ "${PXC_MAJOR_VERSION}" == "5.7" ]]; then
    wget -q https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb
    sudo dpkg -i percona-release_latest.$(lsb_release -sc)_all.deb
    sudo percona-release enable pxb-24 testing
    sudo apt update -y
    sudo apt install -y percona-xtrabackup-24
  fi
fi

# Install pytest correctly for different versions
if [[ "$(lsb_release -sc)" == "bookworm" ]]; then
  pip3 install --user --break-system-packages pytest-testinfra pytest
else
  pip3 install --user pytest-testinfra pytest
fi  

# Extract MySQL tarball
TARBALL_NAME=$(find . -maxdepth 1 -name '*.tar.gz' -o -name '*.deb' -o -name '*.rpm' | head -n1 | xargs basename)
if [[ -z "${TARBALL_NAME}" ]]; then
  echo "ERROR: No PXC tarball found in the current directory!"
  exit 1
fi

tar xf "${TARBALL_NAME}"
PXC_DIR_NAME="${TARBALL_NAME%.tar.gz}"
PXC_DIR_NAME="${PXC_DIR_NAME%.deb}"
PXC_DIR_NAME="${PXC_DIR_NAME%.rpm}"

export BASE_DIR="${PWD}/${PXC_DIR_NAME}"
cp conf/*cnf "$BASE_DIR/" || echo " No custom MySQL configuration files found."

echo "Running tests..."
echo "Test Directory: ${PXC_DIR_NAME}"
python3 -m pytest --ignore="${PXC_DIR_NAME}/percona-xtradb-cluster-tests" -v --junit-xml report.xml "$@"
