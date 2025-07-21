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
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # <span style="color: #de4815"><b>BGP</b></span> DCN Configuration Information
#
# Once the BGP DCN configuration has been added, either through the provided book (BGP_ClosBuilder) or manually, this book will provide you with commands to view information about the configuration of individual nodes in the topology.

# %% [markdown]
# ## <span style="color: #de4815"><b>Topology Information</b></span>
#
# | Variable | Use |
# | --- | --- |
# | SLICE_NAME    | Name of the slice you want to access and observe |
# | NETWORK_NODE_PREFIXES    | The naming prefix(es) for BGP-speaking nodes |
# | COMPUTE_NODE_PREFIXES | The naming prefix(es) for compute/non-BGP-speaking nodes |

# %%
SLICE_NAME = "clos_bgp"
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"

# %% [markdown]
# ## <span style="color: #de4815"><b>Access Slice Resources</b></span>
#
# The FabOrchestrator class is used to grab information. This is a class that wraps around the underlying FabLib to make certain actions easier to run.

# %%
from FabUtils import FabOrchestrator

try:
    manager = FabOrchestrator(SLICE_NAME)
    
except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #de4815"><b>View Routing</b></span>
#
# Anything involing how Linux kernel routing table.

# %%
# Grab the IP Routing table from each BGP node.
print("ROUTING TABLES ON BGP NODES\n")

routingTableCommand = "ip route"
manager.executeCommandsParallel(routingTableCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
# Grab the IP Routing table from each compute node.
print("ROUTING TABLES ON COMPUTE NODES\n")

routingTableCommand = "ip route"
manager.executeCommandsParallel(routingTableCommand, prefixList=COMPUTE_NODE_PREFIXES)

# %%
# Grab the interface status from each node (regardless of the type of node).
print("NETWORK INTERFACE STATUS\n")

intfStatusCmd = "ip address | grep eth"
manager.executeCommandsParallel(intfStatusCmd, prefixList=NETWORK_NODE_PREFIXES)

# %%
# Find any interfaces that are set to down
print("CHECK IF INTERFACES ARE DOWN\n")

intfStatusCmd = "ip address | grep DOWN"
manager.executeCommandsParallel(intfStatusCmd, prefixList=NETWORK_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #de4815"><b>View Configuration</b></span>
#
# Anything involving how FRR or a FABRIC book configures the BGP daemon on the slices.

# %%
outputConfigCommand = 'sudo vtysh -c "show run"'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
outputConfigCommand = 'ls -alt ~/bgp_scripts'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
outputConfigCommand = 'ls -alt /var/log/frr'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
outputConfigCommand = 'tmux kill-session -t bgp'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
outputConfigCommand = 'sudo pkill tshark'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
outputConfigCommand = 'tmux ls'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %%
outputConfigCommand = 'ps aux | grep bash'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #de4815"><b>Modify Configuration - BGP & BGP Testing</b></span>
#
# <b>WARNING</b>: This will potentially modify how BGP or the BGP testing suite operates. Only run these if you need to make that specific change, you shouldn't run anything in this section just to try it out. If something breaks, you'll need to find a way back by adding additional commands here or by manual reconfiguration.

# %%
# Uploading the (local) bgp_scripts directory
manager.uploadDirectoryParallel("/home/fabric/work/custom/FABRIC-Automation/remote_scripts/bgp_scripts", prefixList=NETWORK_NODE_PREFIXES)

# %%
# Updating permission of scripts in the (remote) bgp_scripts directory
manager.executeCommandsParallel('chmod +x /home/rocky/bgp_scripts/*.sh ; chmod +x /home/rocky/bgp_scripts/*.py', prefixList=NETWORK_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #de4815"><b>Modify Configuration - BFD</b></span>
#
# <b>WARNING</b>: This will potentially modify how BFD 

# %%
# Disable BFD
manager.executeCommandsParallel('sudo vtysh -c "conf t" -c "bfd" -c "profile lowerIntervals" -c "shutdown"', prefixList=NETWORK_NODE_PREFIXES)

# %%
# Enable BFD 
manager.executeCommandsParallel('sudo vtysh -c "conf t" -c "bfd" -c "profile lowerIntervals" -c "no shutdown"', prefixList=NETWORK_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #de4815"><b>View Logging</b></span>
#
# The Clos Builder script logs all BGP UPDATE events to /var/log/bgpd.log

# %%
# Grab the IP Routing table from each BGP node.
print("LOG ENTRIES\n")

routingTableEntry = "PAPP6-VDAWM"
routingTableCommand = f"sudo cat /var/log/frr/bgpd.log | grep {routingTableEntry}"
manager.executeCommandsParallel(routingTableCommand, prefixList=NETWORK_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #de4815"><b>Renew Slice</b></span>
#
# Need to keep the slice going? renew it for X number of days. There is a limit of 2 weeks per renewal.

# %%
days_to_renew = 7 # Replace this with a value of 1-14 days

manager.renewSlice(days_to_renew)
