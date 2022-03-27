#!/usr/bin/env bash

source /etc/os-release

WORKDIR="${PWD}/bot/"

if [[ ${NAME} =~ "Debian" ]] || [[ ${NAME} =~ "Ubuntu" ]]; then
    # Debian
    sudo apt-get install -y python3-venv python3 git
elif [[ ${NAME} =~ "CentOS" ]]; then
    # CentOS
    sudo yum install -y python3 git
elif [[ ${NAME} =~ "Fedora" ]]; then
    # CentOS
    sudo dnf install -y python3 git
fi

# Clone the sources
git clone https://github.com/E-Gideon/CyberReaper.git ${WORKDIR}
pushd bot
git submodule update --init --recursive

# Setup the Virtual Environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r ${WORKDIR}/src/MHDDoS/requirements.txt

pushd ${WORKDIR}/src/

python main.py

popd
popd
