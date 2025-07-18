#!/bin/bash

# Stop on the first error if something goes wrong.
set -euo pipefail

# frr-stable will be the latest official stable release. This can be changed if you're looking for a specific version of FRR.
FRRVER="frr-stable"
REPO_RPM="https://rpm.frrouting.org/repo/${FRRVER}-repo.el8.noarch.rpm"

curl -fL --retry 5 --retry-connrefused --retry-delay 2 -o /tmp/frr-repo.rpm "$REPO_RPM"
sudo dnf -y install /tmp/frr-repo.rpm
sudo dnf -y install frr frr-pythontools

# Give permissions to user to access frr files (this requires a logout after to take effect)
sudo usermod -a -G frr,frrvty $(logname)

# Install Python and friends for traffic analysis
sudo dnf install -y $(cat ~/bgp_scripts/required_packages.txt)
sudo python3 -m pip install scapy psutil

# Turn on IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# A "here" document to get around the logout/login requirements of adding a group to a user
newgrp frr << END
sudo sed -i 's/bgpd=no/bgpd=yes/g' /etc/frr/daemons
sudo sed -i 's/bfdd=no/bfdd=yes/g' /etc/frr/daemons
sudo sed -i 's/#frr_profile="datacenter"/frr_profile="datacenter"/g' /etc/frr/daemons
sudo cp bgp_scripts/frr.conf /etc/frr/frr.conf
sudo service frr start
END

echo "BGP-DCN initialization script has finished."
