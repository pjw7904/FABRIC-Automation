"""
Author: Peter Willis
Desc: Class to help build Clos topologies and the node attributes required.
"""

import networkx as nx
from copy import deepcopy

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
       
    def generateNodeName(self, prefix, nodeNum, currentTier, topTier):
        """
        Determine what a given node should be named. The format of a name is node_title-pod_prefix-num for all nodes minus the top tier, which do not use a pod_prefix.

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

    
    def addConnectionToGraph(self, northNode, southNode, northTier, southTier):
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
            nodeNum = 0 # The number associated with a given node, appended after the prefix (ex: 1-1-1, pod 1-1, node number 1)

            for node in range(1,currentPodNodes+1):
                northNode = self.generateNodeName(currentPrefix, str(node), currentTier, topTier)

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

                    southNode = self.generateNodeName(southPrefix, str(southNodeNum), currentTier-1, topTier)

                    self.addConnectionToGraph(northNode, southNode, currentTier, currentTier-1)

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