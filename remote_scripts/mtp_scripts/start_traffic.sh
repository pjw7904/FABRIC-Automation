#!/bin/bash

usage() {
  echo "Usage:"
  echo "  Send mode:    $0 -s <server_ip> -c <count>"
  echo "  Receive mode: $0 -r"
  exit 1
}

RECEIVE_MODE=0
SERVER_IP=""
COUNT=""

while getopts ":s:c:r" opt; do
  case ${opt} in
    s )
      SERVER_IP=$OPTARG
      ;;
    c )
      COUNT=$OPTARG
      ;;
    r )
      RECEIVE_MODE=1
      ;;
    \? )
      usage
      ;;
  esac
done

# Validate arguments
if [ "$RECEIVE_MODE" -eq 0 ]; then
  if [ -z "$SERVER_IP" ] || [ -z "$COUNT" ]; then
    usage
  fi
fi


echo "----------------------------------------"
echo "Traffic Generator Setup"
echo "Host: $(hostname)"
echo "----------------------------------------"

if [ "$RECEIVE_MODE" -eq 1 ]; then
  echo "Mode: RECEIVER"
else
  echo "Mode: SENDER"
  echo "Destination IP: $SERVER_IP"
  echo "Packet Count:   $COUNT"
fi

echo "----------------------------------------"


# Remove prior traffic log files
sudo rm -f ~/Basic-Traffic-Generator/*.txt


# Kill prior tmux session if it exists
tmux has-session -t traffic 2>/dev/null
if [ $? -eq 0 ]; then
  echo "Existing tmux session found - killing it."
  tmux kill-session -t traffic
fi


# Determine command
if [ "$RECEIVE_MODE" -eq 1 ]; then
  CMD="cd ~/Basic-Traffic-Generator && sudo python3 TrafficGenerator.py -r"
else
  CMD="cd ~/Basic-Traffic-Generator && sudo python3 TrafficGenerator.py -s $SERVER_IP -c $COUNT"
fi


# Start tmux session
tmux new-session -d -s traffic "$CMD"

echo "Traffic generator started in tmux session 'traffic'"
echo "----------------------------------------"
echo "Script has finished"