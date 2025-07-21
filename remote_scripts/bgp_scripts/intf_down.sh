#!/bin/bash
# intf_down.sh  <interface>  [soft_failure_bool]

set -euo pipefail
LOGFILE="/home/rocky/bgp_scripts/intf_down.log"

#---------------------------------------------------
# 1. Timestamp is always written first
#---------------------------------------------------
date +"%Y/%m/%d %H:%M:%S.%3N" > "$LOGFILE"

#---------------------------------------------------
# 2. Helper for any kind of failure
#    - appends to log
#    - mirrors to stderr
#---------------------------------------------------
fail() {
    local msg="$1"
    echo "ERROR: $msg" >> "$LOGFILE"
    echo "ERROR: $msg" >&2
    exit 1
}

#---------------------------------------------------
# 3. Argument checks
#---------------------------------------------------
[[ $# -ge 1 ]] || fail "missing interface argument"

INTF="$1"
SOFT="${2:-false}"
SOFT="${SOFT,,}"          # normalise to lower-case

#---------------------------------------------------
# 4. Inject failure
#---------------------------------------------------
case "$SOFT" in
    true|1|yes|y)
        sudo tc qdisc replace dev "$INTF" root netem loss 100% \
            || fail "tc netem injection failed on $INTF"
        ;;
    false|0|no|n|"")
        sudo ip link set dev "$INTF" down \
            || fail "ip link down failed on $INTF"
        ;;
    *)  fail "invalid soft_failure_bool '$2'" ;;
esac

#---------------------------------------------------
# 5. Success — nothing more to write
#---------------------------------------------------
exit 0
