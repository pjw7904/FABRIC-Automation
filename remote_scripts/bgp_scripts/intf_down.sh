#!/bin/bash
# intf_down.sh  <interface>  [soft_failure_bool]  [start_epoch]
#   <interface>        eth1, ens3, …
#   [soft_failure_bool] 0|1 (default 0 → hard failure)
#   [start_epoch]      absolute Unix-epoch seconds[.ms] to trigger action

set -euo pipefail
LOGFILE="/home/rocky/bgp_scripts/intf_down.log"

timestamp() { date +"%Y/%m/%d %H:%M:%S.%3N"; }   # human-readable
epoch_ms()  { date +%s.%3N; }                    # seconds.milliseconds

TIME_WRITTEN=0
write_timestamp_once() {
    if [[ $TIME_WRITTEN -eq 0 ]]; then
        printf "%s\n" "$(timestamp)" > "$LOGFILE"
        TIME_WRITTEN=1
    fi
}

fail() {
    write_timestamp_once                 # ensure ts is first line
    echo "ERROR: $1" >> "$LOGFILE"
    echo "ERROR: $1" >&2
    exit 1
}

# ─────────── 0. Parse args ───────────────────────────────────────────────
[[ $# -ge 1 ]] || fail "Usage: $0 <interface> [soft_bool] [start_epoch]"

INTF="$1"
SOFT="${2:-0}"
START_AT="${3:-}"          # empty → start immediately

case "$SOFT" in
    1|true|yes|y) SOFT=1 ;;
    0|false|no|n|"") SOFT=0 ;;
    *) fail "Invalid soft_failure_bool '$2'" ;;
esac

# ─────────── 1. Optional wait-until ──────────────────────────────────────
if [[ -n "$START_AT" ]]; then
    now=$(epoch_ms)
    wait=$(awk -v t="$START_AT" -v n="$now" 'BEGIN {print t-n}')
    if (( $(awk 'BEGIN {print ('"$wait"' > 0)}') )); then
        sleep "$wait" || fail "sleep interrupted"
    fi
fi

# ─────────── 2. Timestamp just before action ─────────────────────────────
write_timestamp_once          # first line in the log (post-wait)

# ─────────── 3. Inject link failure ──────────────────────────────────────
if [[ $SOFT -eq 1 ]]; then
    sudo tc qdisc replace dev "$INTF" root netem loss 100% \
        || fail "tc netem failed on $INTF"
else
    sudo ip link set dev "$INTF" down \
        || fail "ip link down failed on $INTF"
fi

exit 0     # success → only the timestamp line is in the log
