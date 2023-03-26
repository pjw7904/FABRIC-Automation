#!/bin/bash

# Refresh packages
sudo yum check-update

# tmux installation
sudo yum -y install tmux

# TShark installation
sudo yum -y install wireshark