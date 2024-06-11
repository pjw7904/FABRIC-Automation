# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # <span style="color: #034694"><b>MTP</b></span> Reconvergence Experiment

# %% [markdown]
# A MTP experiment consists of turning off an active control interface (i.e., not an interface on a compute node or an interface on a leaf attached to a compute subnet). The resulting behavior from the generated MTP messages that withdraw the necessary root VID are collected via log files to show how the MTP implementation handles the change.
#
# The steps this book takes are as follows:
#
# 1. <span style="color: #034694"><b>Store test infrastructure information</b></span>
#
# 2. <span style="color: #034694"><b>Clear the exisiting MTP log file</b></span>
# ---
# ```bash
# sudo rm MTP_*.log # Delete the mtp implementation log
# ```
# ---
#
# 3. <span style="color: #034694"><b>Start the MTP implementation and complete initial convergence</b></span>
#
# 4. <span style="color: #034694"><b>Bring the interface down.</b></span>
#
# This can be acomplished in two different ways, either by already knowing the interface name (ethX), or querying FABRIC to determine the interface name.
#
# ---
# ```bash
# sudo ip link set dev ethX down # X = interface number (ex: X = 1, eth1)
# ```
# ---
#
# 5. <span style="color: #034694"><b>Collect the logs</b></span>
# ---
# ```bash
# # Route withdraw
# 2024/04/13 19:57:01.336 BGP: [PAPP6-VDAWM] 172.16.8.1(S-1-1) rcvd UPDATE about 192.168.2.0/24 IPv4 unicast -- withdrawn
# ```
# ---
#
# 6. <span style="color: #034694"><b>Bring the interface back up.</b></span>

# %% [markdown]
# ## <span style="color: #034694"><b>Infrastructure Information</b></span>

# %%
# Slice information
SLICE_NAME = "mtp_test"
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"

# Failure point
NODE_TO_FAIL_INTF = "L-1"
NEIGHBOR_LOST = None
INTF_NAME_KNOWN = True
INTF_NAME = "eth2"

# Local directory location (where to download remote logs)
LOG_DIR_PATH = "../logs/mtp/first_attempt"

# %%
import os
import time

# Remote log locations
lOG_NAME = "/home/rocky/mtp.log"
LOG_INTF_DOWN_NAME = "/home/rocky/mtp_scripts/intf_down.log"

# If the logs directory does not already exist, create it
subdirs = ["convergence", "traffic"]
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
# ## <span style="color: #034694"><b>Implementation Startup & Initial Convergence</b></span>

# %%
# Start the MTP implementation.
startCmd = "bash ~/mtp_scripts/mtp_data_collection.sh"

# First on Spines
manager.executeCommandsParallel(startCmd, prefixList="S,T")
print("Started MTP on spines")

# Wait a bit
print("pausing for spines to start...")
time.sleep(10)

# Then on Leaves
manager.executeCommandsParallel(startCmd, prefixList="L")
print("Started MTP on Leaves")

print("MTP implementation and data collection started.")

# %% [markdown]
# ## <span style="color: #034694"><b>Run Experiment</b></span>

# %%
if(INTF_NAME_KNOWN):
    intfName = INTF_NAME
else:
    fabricIntf = manager.slice.get_interface(f"{NODE_TO_FAIL_INTF}-intf-{NEIGHBOR_LOST}-p1")
    intfName = fabricIntf.get_device_name()

# %% [markdown]
# ## <span style="color: #034694"><b>Collect Logs</b></span>

# %%
# Download MTP log file.
manager.downloadFilesParallel(os.path.join(LOG_DIR_PATH, "convergence", "{name}_mtp.log"), 
                              lOG_NAME, prefixList=NETWORK_NODE_PREFIXES, addNodeName=True)

# %% [markdown]
# ## <span style="color: #034694"><b>Cleanup</b></span>

# %%
stopLoggingCmd = "tmux kill-session -t mtp"
manager.executeCommandsParallel(stopLoggingCmd, prefixList=NETWORK_NODE_PREFIXES)
print("MTP data collection stopped.")

# %%
# Bring the interface back up.
restoreIntfCmd = f"sudo ip link set dev {intfName} up"

# Run this command only on node NODE_TO_FAIL_INTF 
manager.executeCommandsParallel(restoreIntfCmd, prefixList=NODE_TO_FAIL_INTF)
