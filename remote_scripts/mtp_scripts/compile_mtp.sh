#!/bin/bash

# Download and compile the MTP implementation
# MTP code should be publically available on GitHub and follow the format  https://github.com/{GITHUB_USER}/{MTP_REPO}.git, where GITHUB_USER is your GitHub username and MTP_REPO is the MTP code.
git clone https://github.com/pjw7904/CMTP.git ~/CMTP
cd ~/CMTP/SRC && gcc *.c -o MTPstart

# Place the configuration file in the correct location
cp ~/mtp_scripts/mtp.conf ~/CMTP/SRC/

echo "MTP compilation script has finished. Please check to see if MTP was correctly downloaded and compiled."
