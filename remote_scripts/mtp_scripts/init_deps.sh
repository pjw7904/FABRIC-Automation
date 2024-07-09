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

echo "MTP dependencies script has finished. Please check if everything was installed correctly."
