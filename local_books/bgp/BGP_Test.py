# ---
# jupyter:
#   jupytext:
#     custom_cell_magics: kql
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: fabric
#     language: python
#     name: python3
# ---

# %% [markdown]
# # <span style="color: #de4815"><b>BGP</b></span> Reconvergence Experiment

# %% [markdown]
# A BGP experiment consists of turning off an active control interface (i.e., not an interface on a compute node or an interface on a leaf attached to a compute subnet). The resulting behavior from the generated BGP UPDATE messages that withdraw the necessary routes are collected via:
#     
# 1. log files to show how the FRR BGP implementation handles the updates.
# 2. Packet captures that collect the BGP UPDATE messages that the BGP implementation uses to make modifications.
#
# The steps this book takes are as follows:
#
# 1. <span style="color: #de4815"><b>Store test infrastructure information</b></span>
#
# 2. <span style="color: #de4815"><b>Clear all existing bgpd (FRR BGP-4 daemon) logs</b></span>
# ---
# ```bash
# sudo truncate -s 0 /location/of/frr/bgpd/log # Delete the bgpd UPDATE log entries
# sudo rm /location/of/scripts/captures        # Delete the bgpd traffic entries
# sudo rm /location/of/scripts/logs            # Delete additional bgpd-related logs
# ```
# ---
#
# 3. <span style="color: #de4815"><b>Bring the interface down.</b></span>
#
# This can be acomplished in two different ways, either by already knowing the interface name (ethX), or querying FABRIC to determine the interface name.
#
# ---
# ```bash
# sudo ip link set dev ethX down # X = interface number (ex: X = 1, eth1)
# ```
# ---
#
# 4. <span style="color: #de4815"><b>Collect the logs</b></span>
# ---
# ```bash
# # Route withdraw
# 2024/04/13 19:57:01.336 BGP: [PAPP6-VDAWM] 172.16.8.1(S-1-1) rcvd UPDATE about 192.168.2.0/24 IPv4 unicast -- withdrawn
# ```
# ---

# %% [markdown]
# ## <span style="color: #de4815"><b>Experiment Information</b></span>
#
# Every variable presented in the traditional Python constant fomat, ALL_CAPS, should be updated with the expected information. If interface names are not known, that is ok, please just set it to the data type None. 

# %%
# Slice information
SLICE_NAME = "clos_bgp"

NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"

# Experiment information
IS_SOFT_FAILURE = False

NODE_TO_FAIL = "L-1-1"
NODE_INTF_NAME = "eth1"

NEIGHBOR_TO_FAIL = "S-1-1"
NEIGHBOR_INTF_NAME = "eth1"

LOG_DIR_PATH = "/home/pjw7904/fabric/FABRIC-Automation/local_books/bgp/BGP_logs/bgp_soft_failure_bfd/test_6" # Local directory location (where to download remote logs)

# %%
# Get acccess to FabUtils in the local_books dir first
import sys
sys.path.append('..')

# Then proceed with the rest of the imports (including FabUtils)
from FabUtils import FabOrchestrator
from datetime import datetime, timedelta, timezone

try:
    manager = FabOrchestrator(SLICE_NAME)

except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #de4815"><b>Run Experiment</b></span>

# %% [markdown]
# ### Determine failure type and build structures

# %%
INTF_NAMES_KNOWN = True if NODE_INTF_NAME and (NEIGHBOR_INTF_NAME or IS_SOFT_FAILURE) else False

print(f"{'Soft' if IS_SOFT_FAILURE else 'Hard'} link failure experiment to be performed on link {NODE_TO_FAIL} <--> {NEIGHBOR_TO_FAIL}")

# %%
# Determine the interface of the node to be failed
failure_dict = {NODE_TO_FAIL: {"intfName": NODE_INTF_NAME if NODE_INTF_NAME 
                               else manager.getInterfaceName(NODE_TO_FAIL, NEIGHBOR_TO_FAIL)}}

FAILED_NODE_PREFIXES = NODE_TO_FAIL
print(f"{NODE_TO_FAIL} interface name: {failure_dict[NODE_TO_FAIL]["intfName"]}")

# If the failure is a hard link failure, determine the interface on the neighbor of the link that is to be failed as well
if(not IS_SOFT_FAILURE):
    failure_dict[NEIGHBOR_TO_FAIL] = {"intfName": NEIGHBOR_INTF_NAME if NEIGHBOR_INTF_NAME 
                                       else manager.getInterfaceName(NEIGHBOR_TO_FAIL, NODE_TO_FAIL)}
    
    FAILED_NODE_PREFIXES += f",{NEIGHBOR_TO_FAIL}"
    print(f"{NEIGHBOR_TO_FAIL} interface name: {failure_dict[NEIGHBOR_TO_FAIL]["intfName"]}")

# %% [markdown]
# ### Create an experiment log directory

# %%
from pathlib import Path
import time

# Remote log locations
lOG_FRR_NAME = "/var/log/frr/bgpd.log"
LOG_CAP_NAME = "/home/rocky/bgp_scripts/bgp_update_only.pcap"
LOG_OVERHEAD_NAME = "/home/rocky/bgp_scripts/overhead.log"
LOG_INTF_DOWN_NAME = "/home/rocky/bgp_scripts/intf_down.log"

# Local log locations
subdirs = ["captures", "overhead", "convergence"]
baseLogDir = Path(LOG_DIR_PATH)
for sub in subdirs:
    (baseLogDir / sub).mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ### Start data collection on BGP switches

# %%
# Start data collection for nodes
startLoggingCmd = "bash ~/bgp_scripts/bgp_data_collection.sh"
manager.executeCommandsParallel(startLoggingCmd, prefixList=NETWORK_NODE_PREFIXES, excludedList=FAILED_NODE_PREFIXES)

startLoggingCmd += " {intfName}"
manager.executeCommandsParallel(startLoggingCmd, prefixList=FAILED_NODE_PREFIXES, fmt=failure_dict)

print("BGP data collection started.")

# %% [markdown]
# ### Fail the specified link and let BGP reconverge the topology

# %%
print("Giving the nodes time to get configured...")
time.sleep(10)

# %%
# choose a time 5 seconds in the future (same for every node)
start_at = datetime.now(timezone.utc) + timedelta(seconds=5)
start_epoch = f"{start_at.timestamp():.3f}"   # seconds.milliseconds

failIntfCmd = f"bash /home/rocky/bgp_scripts/intf_down.sh {{intfName}} {int(IS_SOFT_FAILURE)} {start_epoch}"

manager.executeCommandsParallel(failIntfCmd, prefixList=FAILED_NODE_PREFIXES, fmt=failure_dict)

# %%
print("Giving the nodes time to get reconverged...")
time.sleep(35)

# %% [markdown]
# ### Experiment teardown

# %%
stopLoggingCmd = "tmux kill-session -t bgp"
manager.executeCommandsParallel(stopLoggingCmd, prefixList=NETWORK_NODE_PREFIXES)
print("BGP data collection stopped.")

# %%
print("Giving the nodes time to process BGP information...")
time.sleep(30)

# %% [markdown]
# ## <span style="color: #de4815"><b>Collect Logs</b></span>

# %%
capture_local   = baseLogDir / "captures"    / "{name}_update.pcap"
overhead_local  = baseLogDir / "overhead"    / "{name}_overhead.log"
frr_local       = baseLogDir / "convergence" / "{name}_frr.log"
intf_down_local = baseLogDir / "convergence" / "{name}_intf_down.log"

# BGP message captures
manager.downloadFilesParallel(
    capture_local, LOG_CAP_NAME,
    prefixList=NETWORK_NODE_PREFIXES
)

# Traffic-overhead stats
manager.downloadFilesParallel(
    overhead_local, LOG_OVERHEAD_NAME,
    prefixList=NETWORK_NODE_PREFIXES
)

# FRR daemon logs
manager.downloadFilesParallel(
    frr_local, lOG_FRR_NAME,
    prefixList=NETWORK_NODE_PREFIXES
)

# Interface-down timestamps (only failed nodes)
manager.downloadFilesParallel(
    intf_down_local, LOG_INTF_DOWN_NAME,
    prefixList=FAILED_NODE_PREFIXES
)

# %%
# Create a log file to record information associated with the experiment run
experiment_log_file = baseLogDir / "experiment.log"

failureText = [
    f"Failed node: {NODE_TO_FAIL}",
    f"Interface name: {failure_dict[NODE_TO_FAIL]['intfName']}",
    f"Failed neighbor: {NEIGHBOR_TO_FAIL}",
    f"Neighbor interface name: {failure_dict[NEIGHBOR_TO_FAIL]['intfName'] if not IS_SOFT_FAILURE else 'N/A'}",
    f"Experiment type: {'soft' if IS_SOFT_FAILURE else 'hard'} link failure"
]

experiment_log_file.write_text("\n".join(failureText))

# %% [markdown]
# ## <span style="color: #de4815"><b>Cleanup</b></span>

# %%
# Bring the interface back up.
if(IS_SOFT_FAILURE):
    # Remove the DROP rules that were added for starvation
    restoreIntfCmd = (
        "sudo iptables -D INPUT  -i {intfName} -j DROP 2>/dev/null || true && "
        "sudo iptables -D OUTPUT -o {intfName} -j DROP 2>/dev/null || true"
    )
else:
    # Re-enable the link for a hard failure
    restoreIntfCmd = "sudo ip link set dev {intfName} up"

# Run on the node(s) where the interface was failed
manager.executeCommandsParallel(
    restoreIntfCmd,
    prefixList=FAILED_NODE_PREFIXES,
    fmt=failure_dict
)
