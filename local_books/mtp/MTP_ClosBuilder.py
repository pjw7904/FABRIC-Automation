# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: fabric
#     language: python
#     name: python3
# ---

# %% [markdown]
# # <span style="color: #034694"><b>MTP</b></span> Folded-Clos Builder
#
# This book provides the following actions:
#
# 1. Building a folded-Clos topology.
# 2. Downloading the MTP implementation as the network control-plane and data-plane on the folded-Clos topology.
# 3. Configuring IPv4 addressing on all devices in the compute/server subnets in the topology. This includes the compute devices themselves and the leaf interfaces connected to these subnets.
# 4. Logging the resulting topology information in a JSON file.

# %% [markdown]
# ## <span style="color: #034694"><b>Input Required Information</b></span>
#
# ### <span style="color: #034694"><b>FABRIC Configuration</b></span> 
# | Variable | Use |
# | :-- | --- |
# | SLICE_NAME| Name of slice you want to create. Please make sure a slice with that name does not already exist. |
# | SITE_NAME| Name of the FABRIC site you want the nodes to be reserved at. This code does not consider inter-site situations, the entire topology is reserved on a single slice. |
# | MEAS_ADD      | Enter True if measurements are to be taken on the slice. This requires the inclusion of a separate measurement node. If you don't understand how to use the Measurement Framework, don't set this to true. |
#
# ### <span style="color: #034694"><b>Folded-Clos Configuration</b></span>
# | Variable | Use |
# | :-- | --- |
# | PORTS_PER_DEVICE     | The number of interfaces every networking device will share in the folded-Clos topology. This must be an even number to split the number of interfaces for north and south links. |
# | NUMBER_OF_TIERS     | The number of tiers the folded-Clos topology will have. It should be 2 or greater. Don't get crazy with the values, FABRIC can only handle so much. |
# | NETWORK_NODE_PREFIXES    | The naming prefix(es) for MTP-speaking nodes |
# | COMPUTE_NODE_PREFIXES | The naming prefix(es) for compute/non-MTP-speaking nodes |
# | SOUTHBOUND_PORT_DENSITY | If you want to change how many southbound ports are used for a device at a given tier, it needs to be placed in a dictonary with the key being the tier and the value being the updated southbound port density. For example, If I want tier 3 spines to only have 2 southbound ports, I would modify this variable to show {3:2}. |
# | MTP_SCRIPTS_LOCATION     | The full path to the mtp_scripts directory. Don't change the name of the files inside of the directory unless you change it in this book as well. |
# | TEMPLATE_LOCATION     | The full path to the MTP Mako template. You don't need to understand how Mako works, the book takes care of it. Don't change the name of the files inside of the directory unless you change it in this book as well. |

# %%
# FABRIC Configuration
SLICE_NAME = "clos_mtp"
SITE_NAME = "MASS"

# Folded-Clos Configuration
PORTS_PER_DEVICE = 4
NUMBER_OF_TIERS = 3
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"
SOUTHBOUND_PORT_DENSITY = {1:1}
MTP_SCRIPTS_LOCATION = "/home/pjw7904/fabric/FABRIC-Automation/remote_scripts/mtp_scripts"
TEMPLATE_LOCATION = "/home/pjw7904/fabric/FABRIC-Automation/remote_scripts/mtp_templates/mtp_conf.mako"

# %% [markdown]
# ## <span style="color: #034694"><b>Access the Fablib Library and Confirm Configuration</b></span>

# %%
# Get acccess to FabUtils in the local_books dir first
import sys
sys.path.append('..')

# Then proceed with the rest of the imports (including FabUtils)
from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

try: 
    fablib = fablib_manager()    
    fablib.show_config()

except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #034694"><b>Build a Graph of the Folded-Clos Topology</b></span> 
#
# A custom library, ClosGenerator, is used to build a graph-representation of a folded-Clos topology. MTP configuration is added as attributes to the nodes as the graph is being constructed.

# %%
from ClosGenerator import *

topology = MTPConfig(PORTS_PER_DEVICE, 
                        NUMBER_OF_TIERS, 
                        southboundPortsConfig=SOUTHBOUND_PORT_DENSITY)
topology.buildGraph()
logFile = topology.jsonGraphInfo()

print("MTP configuration complete\n")
print(f"Folded-Clos topology details (Not considering port density changes):\n{topology.getClosStats()}")

# %% [markdown]
# ## <span style="color: #034694"><b>Prepare the MTP Configuration Template</b></span> 
#
# This book uses the Mako template engine to populate MTP-related information into the MTP configuration file (mtp.conf). The per-node MTP configuration is contained in the graph structure built in the prior section. 

# %%
from mako.template import Template

try: 
    mtpTemplate = Template(filename=TEMPLATE_LOCATION)
    print("MTP configuration template loaded.")
    
except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #034694"><b>Parse the folded-Clos Configuration and Create the Slice</b></span> 

# %%
# Create the slice
slice = fablib.new_slice(name=SLICE_NAME)

addedNodes = {} # Visited nodes structure, format = name : nodeInfo

# Add slice-specific information to the log file
logFile.update({"name": SLICE_NAME, "site": SITE_NAME})

# Iterate over each network in the topology and configure each interface connected to the network, and the network itself.
for networkInfo in topology.iterNetwork(fabricFormating=True):
    networkIntfs = [] # Interfaces to be added to the network.
    network = networkInfo[0] # A tuple containing the nodes on the network.
    networkName = networkInfo[1] # The FABRIC network name.

    print(f"Configuring network: {network}")

    # For each node in a given IPv4 subnet within the folded-Clos topology.
    for node in network:
        # If the node has not yet been visited, provide it with the appropriate configuration.
        if(node not in addedNodes):
            # Add the node to the FABRIC slice.
            nodeInfo = slice.add_node(name=node, cores=1, ram=4, image='default_rocky_8', site=SITE_NAME)

            addedNodes[node] = nodeInfo
            print(f"\tAdded node {node} to the slice.")

        else:
            print(f"\tAlready added node {node} to the slice.")

        # Create a name for the node's interface connected to this network and add it to the FABRIC slice.
        intfName = topology.generateFabricIntfName(node, network)        
        netIntf = addedNodes[node].add_component(model='NIC_Basic', name=intfName).get_interfaces()[0]
        networkIntfs.append(netIntf)

    # Add the network to the FABRIC slice.
    slice.add_l2network(name=networkName, interfaces=networkIntfs, type="L2Bridge")
    print(f"\tAdded network {network}")

# %% [markdown]
# ## <span style="color: #034694"><b>Submit the Slice</b></span>

# %%
# %%time

try:
    # Submit Slice Request
    print(f'Submitting the new slice, "{SLICE_NAME}"...')
    slice.submit()
    print(f'{SLICE_NAME} creation done.')

except Exception as e:
    print(f"Slice Fail: {e}")
    traceback.print_exc()

# %% [markdown]
# ## <span style="color: #034694"><b>Provide Initial Configuration to Nodes</b></span> 
#
# If the node is a core (MTP-speaking) node, it will have the MTP implementation downloaded and compiled.
#
# If the node is an edge (non-MTP-speaking) node, it will have the traffic generator code installed.

# %%
from FabUtils import FabOrchestrator

try:
    manager = FabOrchestrator(SLICE_NAME)
    
except Exception as e:
    print(f"Exception: {e}")


# %%
# CONFIGURATION FOR MTP-SPEAKING LEAF AND SPINE NODES
def addMTPConfiguration(node, topology, mtpTemplate):
    '''
    Prepare a node for the MTP implementation to be utilized.
    '''

    # Store tier information
    nodeTemplate = {'tier': topology.getNodeAttribute(node, 'tier'), 'isTopSpine': topology.getNodeAttribute(node, 'isTopTier')}

    # Process the stored information and render a custom mtp.conf.
    nodeMTPData = mtpTemplate.render(**nodeTemplate)

    # Perform the transfer to the node-specific configuration file
    manager.executeCommandsParallel(f'sudo echo -e "{nodeMTPData}" > mtp_scripts/mtp.conf', prefixList=node)

    return

# Upload the scripts directory for all nodes (switches + servers) and provide the correct permissions
manager.uploadDirectoryParallel(MTP_SCRIPTS_LOCATION)
manager.executeCommandsParallel('sudo chmod +x /home/rocky/mtp_scripts/*.sh')

# Configure the switches
for node in topology.iterNodes(noComputeNodes=True):
    addMTPConfiguration(node, topology, mtpTemplate)

# %%
# Commands to execute the bash scripts configuring the nodes
coreNodeConfig = "./mtp_scripts/init_mtp.sh"
edgeNodeConfig = "./mtp_scripts/init_compute.sh"

# Configure core (MTP-speaking) nodes
manager.executeCommandsParallel(coreNodeConfig, prefixList=NETWORK_NODE_PREFIXES)

# Configure edge (non-MTP-speaking) nodes
manager.executeCommandsParallel(edgeNodeConfig, prefixList=COMPUTE_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #034694"><b>Add IPv4 Addressing to Compute Subnet Nodes</b></span> 
#
# This system utilizes the addressing provided by the ClosGenerator module:
#
# * 192.168.0.0/16 is the compute supernet. All compute subnets are given a /24 subnet. Compute devices are given lower addresses (ex: .1) and the leaf node is given a high address (ex: .254)

# %%
from ipaddress import ip_address, IPv4Address, IPv4Network
import re

COMPUTE_SUPERNET = "192.168.0.0/16"

# Iterate through every node in the topology
for node in topology.iterNodes():
    print(f"Configuring IPv4 addressing on node: {node}")
    
    # Pull IPv4 attribute data to configure FABRIC interfaces
    for neighbor, currentAddress in topology.getNodeAttribute(node, 'ipv4').items():
        # Access the interface from FABRIC.
        intfName = f"{node}-intf-{neighbor}-p1" # Naming is a bit strange, but is formatted in FABRIC as such.
        intf = manager.slice.get_interface(intfName)

        # Convert the address and subnet into ipaddress objects for FABRIC processing.
        fabAddress = IPv4Address(currentAddress)
        fabSubnet = IPv4Network(f"{currentAddress}/24", strict=False)

        # Assign the address to the interface.
        intf.ip_addr_add(addr=fabAddress, subnet=fabSubnet)
    
    # For compute nodes, also add a compute supernet route with its attached leaf node as the next-hop.
    if(not topology.isNetworkNode(node)):
        IPGroup = re.search(r"192\.168\.([0-9]{1,3})\.[0-9]{1,3}", currentAddress) # Grab the third octet number.
        thirdOctet = IPGroup.group(1)
        nextHop = f"192.168.{thirdOctet}.254"

        # Add the route to the node
        intf.get_node().ip_route_add(subnet=IPv4Network(COMPUTE_SUPERNET), gateway=IPv4Address(nextHop))

        print(f"\tAdded route to {node}")
    
    print("\tConfiguration complete.")

# %% [markdown]
# ## <span style="color: #034694"><b>Log Topology Information</b></span> 

# %%
# Iterate through every node in the topology
for nodeName in topology.iterNodes():
    tierNumber = topology.getNodeAttribute(nodeName, 'tier')
    logFile[f"tier_{tierNumber}"][nodeName]["ssh"] = manager.slice.get_node(nodeName).get_ssh_command()


# %%
import json 

with open(f'{SLICE_NAME}_k{PORTS_PER_DEVICE}_t{NUMBER_OF_TIERS}_MTP.json', "w") as outfile:
    json.dump(logFile, outfile)
