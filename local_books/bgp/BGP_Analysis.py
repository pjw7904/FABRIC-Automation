# ---
# jupyter:
#   jupytext:
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
# # <span style="color: #de4815"><b>BGP</b></span> Reconvergence Analysis
#
# Once the appropriate log files are collected, the results can be analyzed.

# %% [markdown]
# ## <span style="color: #de4815"><b>Experiment Information</b></span>
#
# Iterate through each valid file in the given directory to determine metric results

# %%
LOG_DIR_PATH = "/home/pjw7904/fabric/FABRIC-Automation/local_books/bgp/BGP_logs/bgp_soft_failure_bfd/test_5"
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"
EXPERIMENT_LOG_FILE = "experiment.log"
DEBUGGING = False

# %%
from pathlib import Path

def getResultsFile(metric_directory):
    directory_path = Path(LOG_DIR_PATH) / metric_directory

    for file_path in directory_path.iterdir():
        if not file_path.is_file():
            continue

        node_name = file_path.stem.split("_", 1)[0]
        
        yield str(file_path), node_name



# %%
import re
import os

HARD_LINK_FAILURE = 1
SOFT_LINK_FAILURE = 2

failedNodes = set()

# Iterate through each line in the file and store the data
experimentLogFile = os.path.join(LOG_DIR_PATH, EXPERIMENT_LOG_FILE)
with open(experimentLogFile) as file:
    for line in file:
        line = line.strip()

        if line.startswith("Failed node:"):
            NODE_TO_FAIL = line.split(":", 1)[1].strip()
            failedNodes.add(NODE_TO_FAIL)

        elif line.startswith("Failed neighbor:"):
            NEIGHBOR_TO_FAIL = line.split(":", 1)[1].strip()
            failedNodes.add(NEIGHBOR_TO_FAIL)

        elif line.startswith("Interface name:"):
            NODE_INTF_NAME = line.split(":", 1)[1].strip()

        elif line.startswith("Neighbor interface name:"):
            NEIGHBOR_INTF_NAME = line.split(":", 1)[1].strip()

        elif line.startswith("Experiment type:"):
            match = re.match(r"Experiment type: (.+?) link failure", line)
            if match:
                    failureType = match.group(1)
                    EXPERIMENT_TYPE = SOFT_LINK_FAILURE if failureType.strip() == "soft" else HARD_LINK_FAILURE
            else:
                raise Exception("Unknown failure type.")

# %% [markdown]
# ## <span style="color: #de4815"><b>Convergence Time</b></span>

# %%
from datetime import datetime
import time

TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S.%f" # Example timestamp in this format: 2024/04/30 04:09:33.947
START_TIME_FILE_NAME = "intf_down.log"
FRR_LOG_FILE_NAME = "frr.log"

UPDATE_LOG_STATEMENT = "rcvd UPDATE"
WITHDRAWN_LOG_STATEMENT = "IPv4 unicast -- withdrawn"

def getEpochTime(timeString):
    '''
    Return a epoch (unix) timestamp based on a standard timestamp.
    '''
    datetimeFormat = datetime.strptime(timeString, TIMESTAMP_FORMAT)
    return int(datetime.timestamp(datetimeFormat) * 1000) # Reduce precision by moving milliseconds into main time string.

def getBGPTimestamp(logEntry):
    '''
    Return only the timestamp from an FRR log entry.
    '''
    return logEntry.split("BGP:")[0].strip()

def getNodeConvergenceTime(logFile):
    '''
    For a given node/log file, determine when the node reached convergence.
    '''

    nodeConvergenceTime = 0

    with open(logFile) as file:
        logEntry = file.readline()
        
        while logEntry:
            if(UPDATE_LOG_STATEMENT in logEntry and WITHDRAWN_LOG_STATEMENT in logEntry):
                if DEBUGGING: print(f"\t{logEntry.rstrip()}")
                
                # Get the epoch timestamp from the log entry.
                entryTime = getBGPTimestamp(logEntry)
                entryTimeEpoch = getEpochTime(entryTime)

                # Find the farthest valid entry from the start of logging.
                nodeConvergenceTime = max(nodeConvergenceTime, entryTimeEpoch)
            
            logEntry = file.readline()
    
    return nodeConvergenceTime

def getStartTime(intfDownFile, startTimestamp, startTimeFormatted):
    '''
    Record the start time, which is the time the interface was disabled.
    '''
    with open(intfDownFile) as file:
        candidateStartTime = file.readline().rstrip()
        canidateStartTimeEpoch = getEpochTime(candidateStartTime)

    if(startTimestamp == 0 or (canidateStartTimeEpoch < startTimestamp)):
        startTimestamp = canidateStartTimeEpoch
        startTimeFormatted = candidateStartTime

    return startTimestamp, startTimeFormatted

# Code starts here
convergenceTimes = [] # Store all of the node's convergence time's.
startTimestamp = 0 # Time when the interface went down.
startTimeFormatted = "" # Standard clock time

if DEBUGGING: print(f"Valid log entries:")

for logFile, _ in getResultsFile("convergence"):
    if(FRR_LOG_FILE_NAME in logFile):
        # Add each node's convergence time to the convergence times list
        convergenceTimes.append(getNodeConvergenceTime(logFile))
        
    elif(START_TIME_FILE_NAME in logFile):
        startTimestamp, startTimeFormatted = getStartTime(logFile, startTimestamp, startTimeFormatted)

if(not convergenceTimes):
    raise Exception(f"No node convergence times found, please check the log directory {LOG_DIR_PATH}.")

if(not startTimestamp):
    raise Exception(f"No start time found, please check the log directory {LOG_DIR_PATH}.")

# Find the change that occured last out of all changes to finalizes network-wide reconvergence.
lastChangeTimestamp = max(convergenceTimes)

# Determine reconvergence time
reconvergenceTime = lastChangeTimestamp - startTimestamp

print(f"\nDown/Start time: {startTimeFormatted}")
print(f"Reconvergence time: {reconvergenceTime} milliseconds")


# %% [markdown]
# ## <span style="color: #de4815"><b>Control Overhead & Blast Radius</b></span>

# %%
def parseOverhead(line):
    '''
    Take the overhead line format, split on the colon delimiter, and then take the second element. 
    Example: "IPv4 Packet Overhead:79" would grab the value 79.
    '''
    return int(line.split(":")[1])

def getOverhead(overheadFile):
    '''
    Read each line of the overhead file and return the value.
    '''
    with open(overheadFile) as file:
        packetOverhead = parseOverhead(file.readline())
        withdrawnRoutesOverhead = parseOverhead(file.readline())
        addedRoutesOverhead = parseOverhead(file.readline())
        
    return packetOverhead, withdrawnRoutesOverhead, addedRoutesOverhead

# Control Overhead values
totalPacketOverhead = 0
totalWithdrawnRoutesOverhead = 0
totalAddedRoutesOverhead = 0

# Blast Radius values
totalNodeCount = 0
effectedNodeCount = 0

for logFile, nodeName in getResultsFile("overhead"):
    if("overhead.log" in logFile):    
        # Control overhead value updates
        packetOverhead, withdrawnRoutesOverhead, addedRoutesOverhead = getOverhead(logFile)

        # Blast radius value updates
        totalNodeCount += 1
        if(packetOverhead > 0 or nodeName in failedNodes):
            effectedNodeCount += 1

        totalPacketOverhead += packetOverhead
        totalWithdrawnRoutesOverhead += withdrawnRoutesOverhead
        totalAddedRoutesOverhead += addedRoutesOverhead
        
blastRadius = (effectedNodeCount/totalNodeCount) * 100

print(f'''Packet Overhead: {totalPacketOverhead} bytes
Withdrawn Routes Overhead: {totalWithdrawnRoutesOverhead} bytes
Added Routes Overhead: {totalAddedRoutesOverhead} bytes''')

print(f"\nBlast radius: {blastRadius:.2f}% of nodes received updated prefix information.")
print(f"\tNodes receiving updated information: {effectedNodeCount}\n\tTotal nodes: {totalNodeCount}")
