#!/bin/bash

# Mark the time
date +"%D %T.%3N" > /home/rocky/bgp_scripts/intf_down.log

# Take the interface down
sudo ip link set dev $1 down