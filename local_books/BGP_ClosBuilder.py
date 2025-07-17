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
# # <span style="color: #de4815"><b>BGP</b></span> Folded-Clos Builder
#
# This book provides the following actions:
#
# 1. Building a folded-Clos topology.
# 2. Installing the FRRouting implementation of BGP-4 as the network control-plane on the folded-Clos topology.
# 3. Tuning the BGP-4 implementation to be compliant to RFC 7938 - Use of BGP for Routing in Large-Scale Data Centers.
# 4. Configuring IPv4 addressing on all interfaces in the topology.
# 5. Logging the resulting topology information in a JSON file.

# %% [markdown]
# ## <span style="color: #de4815"><b>Input Required Information</b></span>
#
# ### <span style="color: #de4815"><b>FABRIC Configuration</b></span> 
# | Variable | Use |
# | :-- | --- |
# | SLICE_NAME| Name of slice you want to create. Please make sure a slice with that name does not already exist. |
# | SITE_NAME| Name of the FABRIC site you want the nodes to be reserved at. This code does not consider inter-site situations, the entire topology is reserved on a single slice. |
# | MEAS_ADD      | Enter True if measurements are to be taken on the slice. This requires the inclusion of a separate measurement node. If you don't understand how to use the Measurement Framework, don't set this to true. |
#
#
# ### <span style="color: #de4815"><b>Folded-Clos Configuration</b></span>
# | Variable | Use |
# | :-- | --- |
# | PORTS_PER_DEVICE     | The number of interfaces every networking device will share in the folded-Clos topology. This must be an even number to split the number of interfaces for north and south links. |
# | NUMBER_OF_TIERS     | The number of tiers the folded-Clos topology will have. It should be 2 or greater. Don't get crazy with the values, FABRIC can only handle so much. |
# | NETWORK_NODE_PREFIXES    | The naming prefix(es) for BGP-speaking nodes |
# | COMPUTE_NODE_PREFIXES | The naming prefix(es) for compute/non-BGP-speaking nodes |
# | SINGLE_COMPUTE_SUBNET     | If you want a leaf to only have one compute subnet, then set this to true. Otherwise, all compute nodes off of a leaf will be contained in their own subnet. |
# | SOUTHBOUND_PORT_DENSITY | If you want to change how many southbound ports are used for a device at a given tier, it needs to be placed in a dictonary with the key being the tier and the value being the updated southbound port density. For example, If I want tier 3 spines to only have 2 southbound ports, I would modify this variable to show {3:2}. |
# | ADD_SEC_NODE | If you want to add a security node to perform experiments with a simulated hacker, set this to true.
# | BGP_SCRIPTS_LOCATION     | The full path to the bgp_scripts directory. Don't change the name of the files inside of the directory unless you change it in this book as well. |
# | TEMPLATE_LOCATION     | The full path to the BGP Mako template. You don't need to understand how Mako works, the book takes care of it. Don't change the name of the files inside of the directory unless you change it in this book as well. |

# %%
# FABRIC Configuration
SLICE_NAME = "clos_bgp"
SITE_NAME = "MASS"
MEAS_ADD = False

# Folded-Clos Configuration
PORTS_PER_DEVICE = 4
NUMBER_OF_TIERS = 3
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"
SEC_NODE_PREFIX = "H"
SINGLE_COMPUTE_SUBNET = False
SOUTHBOUND_PORT_DENSITY = {1:1}
ADD_SEC_NODE = False
BGP_SCRIPTS_LOCATION = "/home/fabric/work/custom/FABRIC-Automation/remote_scripts/bgp_scripts"
TEMPLATE_LOCATION = "/home/fabric/work/custom/FABRIC-Automation/remote_scripts/frr_templates/frr_conf_bgp.mako"

# %% [markdown]
# ## <span style="color: #de4815"><b>Access the Fablib Library and Confirm Configuration</b></span>

# %%
from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

try: 
    fablib = fablib_manager()    
    fablib.show_config()

except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #de4815"><b>Build a Graph of the Folded-Clos Topology</b></span> 
#
# A custom library, ClosGenerator, is used to build a graph-representation of a folded-Clos topology. BGP-4 configuration is added as attributes to the nodes as the graph is being constructed.

# %%
from ClosGenerator import *

topology = BGPDCNConfig(PORTS_PER_DEVICE, 
                        NUMBER_OF_TIERS, 
                        southboundPortsConfig=SOUTHBOUND_PORT_DENSITY, 
                        singleComputeSubnet=SINGLE_COMPUTE_SUBNET,
                        addSecurityNode=ADD_SEC_NODE)
topology.buildGraph()
logFile = topology.jsonGraphInfo()

print("BGP configuration complete\n")
print(f"Folded-Clos topology details (Not considering port density changes and security node additions):\n{topology.getClosStats()}")

# %% [markdown]
# ## <span style="color: #de4815"><b>Prepare the BGP Configuration Template</b></span> 
#
# This book uses the Mako template engine to populate BGP-related information into the default FRR configuration file (frr.conf). The per-node BGP configuration is contained in the graph structure built in the prior section. 

# %%
from mako.template import Template

try: 
    bgpTemplate = Template(filename=TEMPLATE_LOCATION)
    print("FRR-BGP configuration template loaded.")
    
except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #de4815"><b>Parse the folded-Clos Configuration and Create the Slice</b></span> 

# %%
import os

# CONFIGURATION FOR BGP-SPEAKING LEAF AND SPINE NODES
def addBGPConfiguration(node, nodeInfo, topology, bgpTemplate):
    '''
    Prepare a node for the FRR BGP-4 implementation to be installed.
    '''

    # Store information about BGP-speaking neighbors to configure neighborship
    neighboringNodes = []
    
    # Find the node's BGP-speaking neighbors and determine their ASN as well as their IPv4 address used on the subnet shared by the nodes.
    for neighbor, addr in topology.getNodeAttribute(node, 'ipv4').items():
        if(topology.isNetworkNode(neighbor)):
            neighboringNodes.append({'asn':topology.getNodeAttribute(neighbor, 'ASN'), 'ip':topology.getNodeAttribute(neighbor, 'ipv4', node)})

    # In addition to storing neighbor information, store any compute subnets that the node must advertise to neighbors (leaf's only).
    nodeTemplate = {'neighbors':neighboringNodes, 'bgp_asn': topology.getNodeAttribute(node, 'ASN'), 'networks': topology.getNodeAttribute(node, 'advertise')}

    # Process the stored information and render a custom frr.conf.
    nodeBGPData = bgpTemplate.render(**nodeTemplate)

    # Add FABRIC post-boot tasks to get the node ready for FRR installation
    nodeInfo.add_post_boot_upload_directory(BGP_SCRIPTS_LOCATION,'.')
    nodeInfo.add_post_boot_execute(f'sudo echo -e "{nodeBGPData}" > bgp_scripts/frr.conf')
    nodeInfo.add_post_boot_execute('sudo chmod +x /home/rocky/bgp_scripts/*.sh')

    return

# CONFIGURATION FOR NON-BGP-SPEAKING COMPUTE NODES
def addComputeConfiguration(nodeInfo):
    '''
    Prepare a node for traffic testing.
    '''
    nodeInfo.add_post_boot_upload_directory(BGP_SCRIPTS_LOCATION,'.')
    nodeInfo.add_post_boot_execute('sudo chmod +x /home/rocky/bgp_scripts/*.sh') # added sudo to the front of both of them and added all *.sh to execute

    return

# Create the slice
slice = fablib.new_slice(name=SLICE_NAME)

addedNodes = {} # Visited nodes structure, format = name : nodeInfo

# Add slice-specific information to the log file
logFile.update({"name": SLICE_NAME, "site": SITE_NAME, "meas": MEAS_ADD})

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
            if(node.startswith(SEC_NODE_PREFIX)):
                nodeInfo = slice.add_node(name=node, cores=4, ram=4, disk=80, image='default_debian_11', site=SITE_NAME)
            else:
                nodeInfo = slice.add_node(name=node, cores=1, ram=4, image='default_rocky_8', site=SITE_NAME)

            # If the node is a non-compute node, it needs FRR-BGP configuration instructions.
            if(topology.isNetworkNode(node)):
                addBGPConfiguration(node, nodeInfo, topology, bgpTemplate)
            else:
                addComputeConfiguration(nodeInfo)

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
# ## <span style="color: #de4815"><b>Add a Measurement Node (Optional)</b></span> 

# %%
if(MEAS_ADD):
    import mflib 
    print(f"MFLib version  {mflib.__version__} " )

    from mflib.mflib import MFLib

    # Add measurement node to topology using static method.
    MFLib.addMeasNode(slice, disk=100, image='docker_ubuntu_20', site=SITE_NAME)
    print("Measurement node added.")

else:
    print("No measurement node added.")

# %% [markdown]
# ## <span style="color: #de4815"><b>Submit the Slice</b></span>

# %%
# %%time
import json 

try:
    # Submit Slice Request
    print(f'Submitting the new slice, "{SLICE_NAME}"...')
    slice.submit()
    print(f'{SLICE_NAME} creation done.')

except Exception as e:
    print(f"Slice Fail: {e}")
    traceback.print_exc()

# %% [markdown]
# ## <span style="color: #de4815"><b>Initalize the Measurement Framework (Optional)</b></span>
#
# This step both initalizes and instrumentizes the Measurement framework to use Prometheus and Grafana. If ELK is desired, modifications to the cell need to be made.

# %%
if(MEAS_ADD):
    mf = MFLib(SLICE_NAME) # Initalize
    instrumetize_results = mf.instrumentize( ["prometheus"] ) # Instrumentize
    
    # Grafana SSH Tunnel Command
    print(mf.grafana_tunnel)
    print(f"Browse to https://localhost:{mf.grafana_tunnel_local_port}/grafana/dashboards?query=%2A")

# %% [markdown]
# ## <span style="color: #de4815"><b>Provide Initial Configuration to Nodes</b></span> 
#
# If the node is a core (BGP-speaking) node, it will have FRR installed and the BGP daemon (bgpd) turned on as well as configured.
#
# If the node is an edge (non-BGP-speaking) node, it will have the traffic generator code installed.

# %%
from FabUtils import FabOrchestrator

try:
    manager = FabOrchestrator(SLICE_NAME)
    
except Exception as e:
    print(f"Exception: {e}")

# %%
# Commands to execute the bash scripts configuring the nodes
coreNodeConfig = "./bgp_scripts/init_bgp.sh"
edgeNodeConfig = "./bgp_scripts/init_compute.sh"

# Configure core (BGP-speaking) nodes
manager.executeCommandsParallel(coreNodeConfig, prefixList=NETWORK_NODE_PREFIXES)

# Configure edge (non-BGP-speaking) nodes
manager.executeCommandsParallel(edgeNodeConfig, prefixList=COMPUTE_NODE_PREFIXES)

# %% [markdown]
# ## <span style="color: #de4815"><b>Add IPv4 Addressing to All Nodes</b></span> 
#
# This system utilizes the addressing provided by the ClosGenerator module:
#
# * 192.168.0.0/16 is the compute supernet. All compute subnets are given a /24 subnet. Compute devices are given lower addresses (ex: .1) and the leaf node is given a high address (ex: .254)
#
# * 172.16.0.0/12 is the core supernet. All core subnets are given a /24 subnet. Both devices are given lower addresses.

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
        intf = slice.get_interface(intfName)

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
# ## <span style="color: #de4815"><b>Log Topology Information</b></span> 

# %%
# Iterate through every node in the topology
for nodeName in topology.iterNodes():
    tierNumber = topology.getNodeAttribute(nodeName, 'tier')
    logFile[f"tier_{tierNumber}"][nodeName]["ssh"] = manager.slice.get_node(nodeName).get_ssh_command()
    

# %%
with open(f'{SLICE_NAME}_k{PORTS_PER_DEVICE}_t{NUMBER_OF_TIERS}_BGP.json', "w") as outfile:
    json.dump(logFile, outfile)
