"""
Author: Peter Willis
Desc: Class to help build Clos topologies and the node attributes required.
"""

import networkx as nx
from copy import deepcopy
from ipaddress import ip_address, IPv4Address, IPv4Network

class ClosGenerator:
    # Vertex prefixes to denote position in topology
    TOF_NAME = "T"
    SPINE_NAME = "S"
    LEAF_NAME = "L"
    COMPUTE_NAME = "C"

    # Specific tier values
    LOWEST_SPINE_TIER = 2
    LEAF_TIER = 1
    COMPUTE_TIER = 0

    # To be filled in by subclasses built for a specific network protocol.
    PROTOCOL = None

    def __init__(self, k, t, name):
        """
        Initializes a graph and its data structures to hold network information.

        :param k: Degree shared by each node.
        :param t: Number of tiers in the graph.
        :param name: The name you want to give the topology.
        """

        self.clos = nx.Graph(topTier=t)
        
        self.sharedDegree = k
        self.numTiers = t

        self.name = name
        
    def isNotValidClosInput(self):
        """
        Checks if the shared degree inputted is an even number. This confirms that the folded-Clos will have a 1:1 oversubscription ratio.

        :returns: True or false depending on the shared degree value.
        """

        if(self.sharedDegree % 2 != 0):
            return True
        else:
            return False

    def getNodeTitle(self, currentTier, topTier):
        """
        Determine the type of node and give it the name associated with that type. This name is the start of the full node name.

        :param currentTier: The folded-Clos tier that is being anaylzed currently.
        :param topTier: The folded-Clos tier at the top of the topology.
        :returns: The type given to the node.
        """

        if(currentTier == topTier):
            title = self.TOF_NAME    
        elif(currentTier > 1):
            title = self.SPINE_NAME
        elif(currentTier == 1):
            title = self.LEAF_NAME
        else:
            title = self.COMPUTE_NAME

        return title
       
    def generateNode(self, prefix, nodeNum, currentTier, topTier):
        """
        Determine what a given node should be named and create it. The format of a name is node_title-pod_prefix-num for all nodes minus the top tier, which do not use a pod_prefix.

        :param prefix: The prefix for a given tier within a pod in the topology.
        :param nodeNum: A number associated with that specific node.
        :param currentTier: The folded-Clos tier that is being anaylzed currently.
        :param topTier: The folded-Clos tier at the top of the topology.
        :returns: The name given to the node.
        """

        name = self.getNodeTitle(currentTier, topTier)

        if(currentTier == topTier):
            name += "-"
        else:
            name += prefix + "-"

        name += nodeNum

        return name

    def generatePrefix(self, prefix, addition):
        """
        Generate the prefix for a given tier within a pod in the topology.
        
        :param prefix: The starting prefix to modify.
        :param addition: Additional value to add to the starting prefix to create a new prefix.
        :returns: The new prefix.
        """

        return prefix + "-" + addition

    def determinePrefixVisitedStatus(self, prefix, prefixList):
        """
        Determine if the prefix has been visited in the BFS algorithm yet. If it has not, add it to be visited.
        
        :param prefix: The prefix for a given tier within a pod in the topology.
        :param prefixList: The list of visited prefixes (tiers within a pod).
        """

        if(prefix not in prefixList):
            prefixList.append(prefix)

        return

    
    def connectNodes(self, northNode, southNode, northTier, southTier, **kwargs):
        """
        Connect two nodes together via an edge. The nodes must be in adjacent tiers (ex: tier 2 and tier 3). The nodes also understand if their new neighbor is above them (northbound) or below them (southbound). Subclasses specific to a protocol should override this method with its specific attribute needs beyond north-south interconnection. This base method is provided to simply view the output of a given folded-Clos topology.

        :param northNode: The node in tier N.
        :param southNode: The node in tier N-1.
        :param northTier: The tier value N.
        :param southTier: The tier value N-1.
        """
        if(northNode not in self.clos):
            self.clos.add_node(northNode, northbound=[], southbound=[], tier=northTier)
        if(southNode not in self.clos):
            self.clos.add_node(southNode, northbound=[], southbound=[], tier=southTier)

        self.clos.nodes[northNode]["southbound"].append(southNode)
        self.clos.nodes[southNode]["northbound"].append(northNode)
        
        # self.addProtocolConfig(**kwargs)

        self.clos.add_edge(northNode, southNode)

        return

    
    def buildGraph(self):
        """
        Build a folded-Clos with t tiers and each node containing k interfaces. It is built using a modified BFS algorithm, starting with the top tier of the spines and working its way down to the leaf nodes and compute nodes.
        """

        k = self.sharedDegree
        t = self.numTiers
        
        # Check to make sure the input is valid, return an error if not
        if(self.isNotValidClosInput()):
            raise ValueError("Invalid Clos input (must be equal number of north and south links)")
            
        currentTierPrefix = [""] # Queue for current prefix being connected to a southern prefix
        nextTierPrefix = [] # Queue for the prefixes of the tier directly south of the current tier

        currentPodNodes = (k//2)**(t-1) # Number of top-tier nodes
        topTier = t # The starting tier, and the highest tier in the topology
        currentTier = t # Tracking the tiers as it iterates down them

        southboundPorts = k # Start with top-tier having all southbound ports

        while currentTierPrefix:
            currentPrefix = currentTierPrefix.pop(0)
            print(f"Current prefix: {currentPrefix}")
            nodeNum = 0 # The number associated with a given node, appended after the prefix (ex: 1-1-1, pod 1-1, node number 1)

            for node in range(1,currentPodNodes+1):
                northNode = self.generateNode(currentPrefix, str(node), currentTier, topTier)

                for intf in range(1, southboundPorts+1):
                    # Per BFS logic, mark the neighbor as visited if it has not already and add it to the queue.

                    # All tiers > 2.
                    if(currentTier > self.LOWEST_SPINE_TIER):
                        southPrefix = self.generatePrefix(currentPrefix, str(intf))
                        self.determinePrefixVisitedStatus(southPrefix, nextTierPrefix)
                        southNodeNum = (nodeNum%(currentPodNodes // (k//2)))+1

                    # The Leaf tier needs to have the same prefix of the spine tier (tier-2), as that is the smallest unit (pod).
                    elif(currentTier == self.LOWEST_SPINE_TIER):
                        southPrefix = currentPrefix
                        self.determinePrefixVisitedStatus(southPrefix, nextTierPrefix)
                        southNodeNum = intf

                    # Tier 1 connects to Tier 0, the compute nodes.
                    elif(currentTier == self.LEAF_TIER):
                        southPrefix = northNode.strip(self.LEAF_NAME)
                        southNodeNum = intf

                    southNode = self.generateNode(southPrefix, str(southNodeNum), currentTier-1, topTier)

                    self.connectNodes(northNode, southNode, currentTier, currentTier-1)

                nodeNum += 1

            if(not currentTierPrefix):
                currentTierPrefix = deepcopy(nextTierPrefix)
                nextTierPrefix.clear()

                # If the top tier was just connected with its southbound neighbors
                if(currentTier == topTier):
                    southboundPorts = k//2 # All tiers except the top have half of their ports southbound

                    # Proper distribution of links for 2-tier topologies
                    if(topTier == self.LOWEST_SPINE_TIER):
                        currentPodNodes = k

                # The number of connections in the next tier below will be cut down appropriately
                if(currentTier > self.LOWEST_SPINE_TIER):
                    currentPodNodes = currentPodNodes // (k//2)

                currentTier -= 1 # Now that the current tier is complete, move down to the next one

    def logGraphInfo(self, k, t, topTier):
        """
        Output folded-Clos topology information into a log file.
        
        :param k: Degree shared by each node.
        :param t: Number of tiers in the graph.
        :param topTier: The folded-Clos tier at the top of the topology.
        """

        numTofNodes = (k//2)**(t-1)
        numServers = 2*((k//2)**t)
        numSwitches = ((2*t)-1)*((k//2)**(t-1))
        numLeaves = 2*((k//2)**(t-1))
        numPods = 2*((k//2)**(t-2))
        
        with open(f'{k}_{t}_{self.name}.log', 'w') as logFile:
            logFile.write("=============\nFOLDED CLOS\nk = {k}, t = {t}\n{k}-port devices with {t} tiers.\n=============\n".format(k=k, t=t))

            logFile.write("Number of ToF Nodes: {}\n".format(numTofNodes))
            logFile.write("Number of physical servers: {}\n".format(numServers))
            logFile.write("Number of networking nodes: {}\n".format(numSwitches))
            logFile.write("Number of leaves: {}\n".format(numLeaves))
            logFile.write("Number of Pods: {}\n".format(numPods))

            for tier in reversed(range(topTier+1)):
                nodes = [v for v in self.clos if self.clos.nodes[v]["tier"] == tier]
                logFile.write("\n== TIER {} ==\n".format(tier))

                for node in sorted(nodes):
                    logFile.write(node)
                    logFile.write("\n\tnorthbound:\n")
                    
                    for n in self.clos.nodes[node]["northbound"]:
                        logFile.write("\t\t{}\n".format(n))
                        
                    logFile.write("\n\tsouthbound:\n")
                    
                    for s in self.clos.nodes[node]["southbound"]:
                        logFile.write("\t\t{}\n".format(s))
                        
        return


class BGPDCNConfig(ClosGenerator):
    PROTOCOL = "BGP"
    PRIVATE_ASN_RANGE_START = 64512

    LEAF_SPINE_SUPERNET = '172.16.0.0/12'
    COMPUTE_SUPERNET = '192.168.0.0/16'
    LEAF_SPINE_SUBNET_BITS = 12
    COMPUTE_SUBNET_BITS = 8

    def __init__(self, k, t, name):
        """
        Initializes a graph and its data structures to hold network information.

        :param k: Degree shared by each node.
        :param t: Number of tiers in the graph.
        :param name: The name you want to give the topology.
        """

        # Call superclass constructor to get graph setup
        super().__init__(k, t, name)

        # Configure how BGP will assign ASNs and IPv4 addressing
        self.ASNAssignment = {None : None}
        self.currentASN = self.PRIVATE_ASN_RANGE_START
        self.IPAssignment = {}

        self.coreNetworks = list(IPv4Network(self.LEAF_SPINE_SUPERNET).subnets(prefixlen_diff=self.LEAF_SPINE_SUBNET_BITS))
        self.edgeNetworks = list(IPv4Network(self.COMPUTE_SUPERNET).subnets(prefixlen_diff=self.COMPUTE_SUBNET_BITS))
        
    def generateNode(self, prefix, nodeNum, currentTier, topTier):
        """
        Determine what a given node should be named and create it. The format of a name is node_title-pod_prefix-num for all nodes minus the top tier, which do not use a pod_prefix.

        :param prefix: The prefix for a given tier within a pod in the topology.
        :param nodeNum: A number associated with that specific node.
        :param currentTier: The folded-Clos tier that is being anaylzed currently.
        :param topTier: The folded-Clos tier at the top of the topology.
        :returns: The name given to the node.
        """

        title = self.getNodeTitle(currentTier, topTier)

        if(currentTier == topTier):
            partialName = title + "-"
        else:
            partialName = title + prefix + "-"

        # Add the unique number given to this node in the pod.
        name = partialName + nodeNum
            
        # ASN stuff
        ASNPrefix = None

        # Compute nodes don't get an ASN
        if(title != self.COMPUTE_NAME):
            # Every leaf gets its own ASN
            if(title == self.LEAF_NAME):
                ASNPrefix = name

            # Spines in a pod get the same ASN
            elif(title == self.TOF_NAME or title == self.SPINE_NAME):
                ASNPrefix = partialName

            if(ASNPrefix not in self.ASNAssignment):
                self.ASNAssignment[ASNPrefix] = self.currentASN
                self.currentASN += 1

        # I'm not sure if the conditional is needed here in a new function, but it was used successfully in the base class
        if(name not in self.clos):
            self.clos.add_node(name, northbound=[], southbound=[], tier=None, ASN=self.ASNAssignment[ASNPrefix], ipv4={}, advertise=[])

        # Return just the name, not the node object iself
        return name
   
    # Have the origional add **kwags so you can add the prefix?
    def connectNodes(self, northNode, southNode, northTier, southTier, **kwargs):
        """
        Connect two nodes together via an edge. Also configure the BGP ASN number and IP addressing.

        :param northNode: The node in tier N.
        :param southNode: The node in tier N-1.
        :param northTier: The tier value N.
        :param southTier: The tier value N-1.
        """

        NEXT_SUBNET = 0

        # If one of the nodes is a compute node, this is an edge network.
        if(southTier == self.COMPUTE_TIER):
            subnet = list(self.edgeNetworks.pop(NEXT_SUBNET))[:-1] # Remove broadcast address
        else:
            subnet = list(self.coreNetworks.pop(NEXT_SUBNET))[1:-1] # Remove network and broadcast address

        # Assign IP addressing
        if(northTier == self.LEAF_TIER):
            networkAddress = subnet.pop(0)
            northAddress = subnet.pop()
            self.clos.nodes[northNode]["advertise"].append(f"{networkAddress}/24")
        else:
            northAddress = subnet.pop(0)

        southAddress = subnet.pop(0)

        self.clos.nodes[northNode]["southbound"].append(southNode)
        self.clos.nodes[northNode]["tier"] = northTier
        self.clos.nodes[northNode]["ipv4"][southNode] = str(northAddress)

        self.clos.nodes[southNode]["northbound"].append(northNode)
        self.clos.nodes[southNode]["tier"] = southTier
        self.clos.nodes[southNode]["ipv4"][northNode] = str(southAddress)

        self.clos.add_edge(northNode, southNode)

        return

    def logGraphInfo(self, k, t, topTier):
        """
        Output folded-Clos topology information into a log file.
        
        :param k: Degree shared by each node.
        :param t: Number of tiers in the graph.
        :param topTier: The folded-Clos tier at the top of the topology.
        """

        numTofNodes = (k//2)**(t-1)
        numServers = 2*((k//2)**t)
        numSwitches = ((2*t)-1)*((k//2)**(t-1))
        numLeaves = 2*((k//2)**(t-1))
        numPods = 2*((k//2)**(t-2))
        
        with open(f'{k}_{t}_BGP.log', 'w') as logFile:
            logFile.write("=============\nFOLDED CLOS\nk = {k}, t = {t}\n{k}-port devices with {t} tiers.\n=============\n".format(k=k, t=t))

            logFile.write("Number of ToF Nodes: {}\n".format(numTofNodes))
            logFile.write("Number of physical servers: {}\n".format(numServers))
            logFile.write("Number of networking nodes: {}\n".format(numSwitches))
            logFile.write("Number of leaves: {}\n".format(numLeaves))
            logFile.write("Number of Pods: {}\n".format(numPods))

            for tier in reversed(range(topTier+1)):
                nodes = [v for v in self.clos if self.clos.nodes[v]["tier"] == tier]
                logFile.write("\n== TIER {} ==\n".format(tier))

                for node in sorted(nodes):
                    logFile.write(node)
                    logFile.write(f'\n\tASN = {self.clos.nodes[node]["ASN"]}') # BGP ASN printout
                    logFile.write(f'\n\tAdvertised routes: {self.clos.nodes[node]["advertise"]}')
                    logFile.write("\n\tnorthbound:\n")
                    
                    for n in self.clos.nodes[node]["northbound"]:
                        addr = self.clos.nodes[node]["ipv4"][n]
                        logFile.write(f"\t\t{n} - {addr}\n")
                        
                    logFile.write("\n\tsouthbound:\n")
                    
                    for s in self.clos.nodes[node]["southbound"]:
                        #logFile.write("\t\t{}\n".format(s))
                        addr = self.clos.nodes[node]["ipv4"][s]
                        logFile.write(f"\t\t{s} - {addr}\n")
                        
        return