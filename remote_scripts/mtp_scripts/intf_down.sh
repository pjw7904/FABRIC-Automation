#!/bin/bash

# Mark the time
#date +"%Y/%m/%d %H:%M:%S.%3N" > /home/rocky/mtp_scripts/intf_down.log
date +"+%s%3N"

# Take the interface down
sudo ip link set dev $1 down