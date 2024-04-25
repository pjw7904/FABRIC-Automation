#!/bin/bash

# Clear the FRR BGP log file
sudo truncate -s 0 /var/log/frr/bgpd.log

# Remove all pcap files
sudo rm ~/bgp_scripts/*.pcap

# Remove additional log files
sudo rm ~/bgp_scripts/*.log

# Kill the prior session if it is still there for some reason
tmux has-session -t bgp 2>/dev/null
if [ $? == 0 ]; then
  tmux kill-session -t bgp
fi

# Start collecting BGP messages and parse them when the experiment concludes.
tmux new-session -d -s bgp 'cd ~/bgp_scripts && bash bgp_capture_update_messages.sh'

echo "Script has finished"