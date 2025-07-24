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
# ## <span style="color: #034694"><b>Experiment Information</b></span>
# 
# Every variable presented in the traditional Python constant fomat, ALL_CAPS, should be updated with the expected information. If interface names are not known, that is ok, please just set it to the data type None. 

# %%
# Slice information
SLICE_NAME = "clos_mtp"

SPINE_PREFIXES = "T,S"
LEAF_PREFIX = "L"
COMPUTE_NODE_PREFIX = "C"

# Experiment information
IS_SOFT_FAILURE = True

NODE_TO_FAIL = "L-1-1"
NODE_INTF_NAME = "eth2"

NEIGHBOR_TO_FAIL = "S-1-1"
NEIGHBOR_INTF_NAME = "eth4"

LOG_DIR_PATH = "/home/pjw7904/fabric/FABRIC-Automation/local_books/mtp/MTP_logs/mtp_soft_failure/test_3" # Local directory location (where to download remote logs)

# %%
# Get acccess to FabUtils in the local_books dir first
import sys
sys.path.append('..')

# Then proceed with the rest of the imports (including FabUtils)
from FabUtils import FabOrchestrator
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

try:
    manager = FabOrchestrator(SLICE_NAME)

except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #034694"><b>Start MTP</b></span>

# %%
# Start the MTP implementation.
startCmd = "bash ~/mtp_scripts/mtp_data_collection.sh"

# First on Spines
print("Starting MTP on spines...\n")
manager.executeCommandsParallel(startCmd, prefixList=SPINE_PREFIXES)

# Wait a bit
print("pausing for spines to start...")

time.sleep(10)

# Then on Leaves
print("Starting MTP on leaves...\n")
manager.executeCommandsParallel(startCmd, prefixList=LEAF_PREFIX)

print("MTP implementation and data collection started.")

# Wait a bit to allow for MTP initial convergence
print("Giving the nodes time to get converged...")

time.sleep(10)

# %% [markdown]
# ## <span style="color: #034694"><b>Run Experiment</b></span>

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
# Remote log locations
lOG_MTP_NAME = "/home/rocky/mtp.log"
LOG_INTF_DOWN_NAME = "/home/rocky/mtp_scripts/intf_down.log"
LOG_NODE_DOWN_NAME = "/home/rocky/CMTP/SRC/node_down.log"

# Local log locations
subdirs = ["convergence", "downtime"]
baseLogDir = Path(LOG_DIR_PATH)
for sub in subdirs:
    (baseLogDir / sub).mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ### Fail the specified link and let MTP reconverge the topology

# %%
# choose a time 5 seconds in the future (same for every node)
start_at = datetime.now(timezone.utc) + timedelta(seconds=5)
start_epoch = f"{start_at.timestamp():.3f}"   # seconds.milliseconds

failIntfCmd = f"bash /home/rocky/mtp_scripts/intf_down.sh {{intfName}} {int(IS_SOFT_FAILURE)} {start_epoch}"

manager.executeCommandsParallel(failIntfCmd, prefixList=FAILED_NODE_PREFIXES, fmt=failure_dict)

# %%
print("Giving the nodes time to get reconverged...")
time.sleep(35)

# %% [markdown]
# ### Experiment teardown

# %%
NETWORK_NODE_PREFIXES = SPINE_PREFIXES + "," + LEAF_PREFIX

stopMTPCmd ="tmux send-keys -t mtp C-c"

manager.executeCommandsParallel(stopMTPCmd, prefixList=NETWORK_NODE_PREFIXES)
print("MTP data collection stopped.")

# %%
stopTmuxSession = "tmux kill-session -t mtp"

manager.executeCommandsParallel(stopTmuxSession, prefixList=NETWORK_NODE_PREFIXES)
print("MTP Tmux session stopped.")

# %% [markdown]
# ## <span style="color: #034694"><b>Collect Logs</b></span>

# %%
mtp_local       = baseLogDir / "convergence" / "{name}_mtp.log"
intf_down_local = baseLogDir / "downtime" / "{name}_intf_down.log"
mtp_down_local  = baseLogDir / "downtime"    / "nodes_down.log"

nodeDownTimeCmd = f"cat {Path(LOG_NODE_DOWN_NAME)}"

# MTP implementation logs
manager.downloadFilesParallel(
    mtp_local, lOG_MTP_NAME,
    prefixList=NETWORK_NODE_PREFIXES
)

# Interface-down timestamps (only failed nodes)
manager.downloadFilesParallel(
    intf_down_local, LOG_INTF_DOWN_NAME,
    prefixList=FAILED_NODE_PREFIXES
)

# MTP implementation stop logs (aggregated into one log file)
nodeDownTimes = manager.executeCommandsParallel(
    nodeDownTimeCmd,
    prefixList=NETWORK_NODE_PREFIXES,
    returnOutput=True
)
mtp_down_local.parent.mkdir(parents=True, exist_ok=True)

with mtp_down_local.open("w") as node_log_file:
    for node, time in nodeDownTimes.items():
        node_log_file.write(f"{node}:{time}")

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
# ## <span style="color: #034694"><b>Cleanup</b></span>

# %%
# Bring the interface back up.
if IS_SOFT_FAILURE:
    restoreIntfCmd = "sudo nft delete table netdev starvation"
else:
    restoreIntfCmd = "sudo ip link set dev {intfName} up"

manager.executeCommandsParallel(
    restoreIntfCmd,
    prefixList=FAILED_NODE_PREFIXES,
    fmt=failure_dict
)


