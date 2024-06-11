#!/bin/bash

# Remove additional log files
sudo rm ~/*.log

# Kill the prior session if it is still there for some reason
tmux has-session -t mtp 2>/dev/null
if [ $? == 0 ]; then
  tmux kill-session -t mtp
fi

# Start collecting mtp messages and parse them when the experiment concludes.
tmux new-session -d -s mtp "cd ~/CMTP/SRC && sudo ./MTPstart"

echo "Script has finished"