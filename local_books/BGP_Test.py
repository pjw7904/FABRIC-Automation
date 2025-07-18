# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
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
# ## <span style="color: #de4815"><b>Infrastructure Information</b></span>

# %%
# Slice information
SLICE_NAME = "bgp_1pod"
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"

# Failure point
IS_SOFT_FAILURE = True
NODE_FAILED = {
    "name": "L-1",
    "interface": "eth1"
}
NEIGHBOR_FAILED =  {
    "name": None,
    "interface": None
}
INTF_NAMES_KNOWN = True if NODE_FAILED["interface"] and (NEIGHBOR_FAILED["interface"] or IS_SOFT_FAILURE) else False

# Local directory location (where to download remote logs)
LOG_DIR_PATH = "../logs/1209_logs"

print(INTF_NAMES_KNOWN)

# %%
import os
import time

# Remote log locations
lOG_FRR_NAME = "/var/log/frr/bgpd.log"
LOG_CAP_NAME = "/home/rocky/bgp_scripts/bgp_update_only.pcap"
LOG_OVERHEAD_NAME = "/home/rocky/bgp_scripts/overhead.log"
LOG_INTF_DOWN_NAME = "/home/rocky/bgp_scripts/intf_down.log"

# If the logs directory does not already exist, create it
subdirs = ["captures", "overhead", "convergence", "traffic"]
if not os.path.exists(LOG_DIR_PATH):
    for subdir in subdirs:
        os.makedirs(os.path.join(LOG_DIR_PATH, subdir)) 

# %%
from FabUtils import FabOrchestrator

try:
    manager = FabOrchestrator(SLICE_NAME)
    
except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #de4815"><b>Run Experiment</b></span>

# %%
if(INTF_NAMES_KNOWN):
    intfName = FAILED_NODE_INTF_NAME
else:
    fabricIntf = manager.slice.get_interface(f"{NODE_FAILED["name"]}-intf-{NEIGHBOR_FAILED["name"]}-p1")
    intfName = fabricIntf.get_device_name()

# %%
# Start data collection for all nodes minus the one that is being failed.
startLoggingCmd = "bash ~/bgp_scripts/bgp_data_collection.sh"
manager.executeCommandsParallel(startLoggingCmd, prefixList=NETWORK_NODE_PREFIXES, excludedList=NODE_FAILED)

startLoggingCmd = f"bash ~/bgp_scripts/bgp_data_collection.sh {intfName}"
manager.executeCommandsParallel(startLoggingCmd, prefixList=NODE_FAILED)

print("BGP data collection started.")

# %%
print("Giving the nodes time to get configured...")
time.sleep(10)

# %%
failIntfCmd = f"bash /home/rocky/bgp_scripts/intf_down.sh {intfName}"

# Run this command only on node NODE_FAILED 
manager.executeCommandsParallel(failIntfCmd, prefixList=NODE_FAILED)

# %%
print("Giving the nodes time to get reconverged...")
time.sleep(10)

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
# Download BGP message capture file.
manager.downloadFilesParallel(os.path.join(LOG_DIR_PATH, "captures", "{name}_update.pcap"), 
                              LOG_CAP_NAME, prefixList=NETWORK_NODE_PREFIXES, addNodeName=True)

# Download BGP traffic overhead analysis file.
manager.downloadFilesParallel(os.path.join(LOG_DIR_PATH, "overhead", "{name}_overhead.log"), 
                              LOG_OVERHEAD_NAME, prefixList=NETWORK_NODE_PREFIXES, addNodeName=True)

# Download FRR log file.
manager.downloadFilesParallel(os.path.join(LOG_DIR_PATH, "convergence", "{name}_frr.log"), 
                              lOG_FRR_NAME, prefixList=NETWORK_NODE_PREFIXES, addNodeName=True)

# Download the interface downtime log.
manager.downloadFilesParallel(os.path.join(LOG_DIR_PATH, "convergence", "intf_down.log"), 
                              LOG_INTF_DOWN_NAME, prefixList=NODE_FAILED)

# %% [markdown]
# ## <span style="color: #de4815"><b>Cleanup</b></span>

# %%
# Bring the interface back up.
restoreIntfCmd = f"sudo ip link set dev {intfName} up"

# Run this command only on node NODE_FAILED 
manager.executeCommandsParallel(restoreIntfCmd, prefixList=NODE_FAILED)
