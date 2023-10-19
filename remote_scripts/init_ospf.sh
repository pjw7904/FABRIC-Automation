#!/bin/bash

# frr-stable will be the latest official stable release. This can be changed if you're looking for a specific version of FRR.
FRRVER="frr-stable"

# Add RPM repository. This was built for Red Hed 8, but works with Rocky 8 as well.
#    Note: Supported since FRR 7.3
curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el8.noarch.rpm
sudo yum install -y ./$FRRVER*

# install FRR.
sudo yum install -y frr frr-pythontools

# Give permissions to user to access frr files (this requires a logout after to take effect)
sudo usermod -a -G frr,frrvty $(logname)

# Install tshark for packet-level inspections and tmux for multiplexing capabilties if necessary.
sudo dnf install -y tmux wireshark

# This is an example of a here document.
newgrp frr << END
sudo sed -i 's/ospfd=no/ospfd=yes/g' /etc/frr/daemons
sudo service frr start
sudo vtysh -c 'conf t' -c 'router ospf' -c 'network 192.168.0.0/16 area 0'
END

echo "Installation complete!"

# This needs to be updated to something
# command1 = "sudo vtysh -c 'conf t' -c 'inter {0}' -c 'ip ospf hello-interval {1}'".format(port,keepAliveTimer)
# command2 = "sudo vtysh -c 'conf t' -c 'inter {0}' -c 'ip ospf dead-interval {1}'".format(port,holdTimer