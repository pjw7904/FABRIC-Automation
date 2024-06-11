#!/bin/bash

# Install additional packages to properly run the protocol implementation
sudo dnf install -y $(cat ~/mtp_scripts/required_packages.txt)
sudo dnf groupinstall -q -y "Development Tools"
sudo python3 -m pip install scapy psutil

# Turn off IP forwarding
sudo sysctl -w net.ipv4.ip_forward=0

# Configure tmux
echo "tmux pipe-pane -o 'cat >>~/mtp.log'" > ~/tmux_start_logging.sh
sudo chmod 777 ~/tmux_start_logging.sh
echo "set -g remain-on-exit on" > ~/.tmux.conf
echo "set-hook -g after-new-session 'run ~/tmux_start_logging.sh'" >> ~/.tmux.conf

# Download and compile the MTP implementation
git clone https://github.com/pjw7904/CMTP.git ~/CMTP
cd ~/CMTP/SRC && gcc *.c -o MTPstart

# Place the configuration file in the correct location
cp ~/mtp_scripts/mtp.conf ~/CMTP/SRC/

echo "MTP initialization script has finished."