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
# # <span style="color: #034694"><b>MTP</b></span> Reconvergence Analysis
#
# Once the appropriate log files are collected, the results can be analyzed.

# %% [markdown]
# ## <span style="color: #034694"><b>Experiment Information</b></span>
#
# Iterate through each valid file in the given directory to determine metric results

# %%
LOG_DIR_PATH = "/home/pjw7904/fabric/FABRIC-Automation/local_books/mtp/MTP_logs/mtp_soft_failure/test_5"
NETWORK_NODE_PREFIXES = "T,S,L"
COMPUTE_NODE_PREFIXES = "C"
EXPERIMENT_LOG_FILE = "experiment.log"
DEBUGGING = False

# %%
from pathlib import Path

def getResultsFile(metric_directory, includeNodeName=False):
    directory_path = Path(LOG_DIR_PATH) / metric_directory

    for file_path in directory_path.iterdir():
        if not file_path.is_file():
            continue

        node_name = file_path.stem.split("_", 1)[0]

        if(includeNodeName):
            yield str(file_path), node_name
        else:
            yield str(file_path)



# %%
import re
import os

HARD_LINK_FAILURE = 1
SOFT_LINK_FAILURE = 2

failedNodes = set()

# Iterate through each logEntry in the file and store the data
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
# ## <span style="color: #034694"><b>Determine experiment timing bounds</b></span>

# %%
from datetime import datetime, timezone

# Experiment timing log files
START_TIME_FILE_NAME = "intf_down.log"
NODES_DOWN_FILE_NAME = "nodes_down.log"

# Experiment timing log sudirectory
DOWNTIME_DIR = "downtime"

# Format for interface-down timestamp
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S.%f" # Example timestamp in this format: 2024/04/30 04:09:33.947


def getEpochTime(timeString, timestampFormat=TIMESTAMP_FORMAT):
    '''
    Return a epoch (unix) timestamp based on a standard timestamp. Keeps everything in UTC.
    '''

    datetimeFormat = datetime.strptime(timeString, timestampFormat).replace(tzinfo=timezone.utc)
    return int(datetimeFormat.timestamp() * 1000)


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


def getTestStopTime(logFile):
    '''
    Find the stoptime for each node and determine the one that stopped first. That time is the end of the test.
    '''
    testStopTime = 0
    
    with open(logFile) as file:
        lines = file.readlines()

        for line in lines:
            nodeStopTime = int(line.split(":")[1])
            testStopTime = nodeStopTime if nodeStopTime < testStopTime or testStopTime == 0 else testStopTime
    
    return testStopTime


startTimestamp = 0 # Time when the interface went down.
startTimeFormatted = "" # Standard clock time

# Analyze each file in the downtime subdirectory
for logFile in getResultsFile(DOWNTIME_DIR):
    # Determine what the test stoptime was
    if(NODES_DOWN_FILE_NAME in logFile): 
        testStopTime = getTestStopTime(logFile)

    # Determine when the first interface failure occurred
    elif(START_TIME_FILE_NAME in logFile): 
        startTimestamp, startTimeFormatted = getStartTime(logFile, startTimestamp, startTimeFormatted)

    # No idea what this file is, might want to check that out
    else:
        print(f"Unknown file {logFile}")

if(not startTimestamp):
    raise Exception(f"No start time found, please check the log directory {LOG_DIR_PATH}.")

print(f"Down/Start time: {startTimeFormatted} (epoch: {startTimestamp})")
print(f"Test stop time (epoch): {testStopTime}")

#print(f"Interface failure timestamp: {failureTime}\nTest stop timestamp: {testStopTime}")

# %% [markdown]
# ## <span style="color: #034694"><b>Convergence Time</b></span>

# %%
MTP_LOG_FILE_NAME = "mtp.log"

UPDATE_LOG_STATEMENT = "FAILURE UPDATE message received"

def getNodeConvergenceTime(logFile):
    '''
    For a given node/log file, determine when the node reached convergence.
    '''

    nodeConvergenceTime = 0

    with open(logFile) as file:
        logEntry = file.readline()
    
        while logEntry:
            if(UPDATE_LOG_STATEMENT in logEntry):
                token = logEntry.split(" ")
                entryTime = int(token[6].replace(",",""))
    
                if(entryTime < testStopTime):
                    if DEBUGGING: print(f"\t{logEntry.rstrip()}")
                    # Find the farthest valid entry from the start of logging.
                    nodeConvergenceTime = max(nodeConvergenceTime, entryTime)
            
            logEntry = file.readline()
        
    return nodeConvergenceTime

# Default starting values for the timing range
failureDetectionTimestamp = -1
finalFailureRecoveryTimestamp = -1

# Store all of the node's convergence time's.
convergenceTimes = []

for logFile in getResultsFile("convergence"):
    if(MTP_LOG_FILE_NAME in logFile):
        # Add each node's convergence time to the convergence times list
        convergenceTimes.append(getNodeConvergenceTime(logFile))

if(not convergenceTimes):
    raise Exception(f"No node convergence times found, please check the log directory {LOG_DIR_PATH}.")

# Find the change that occured last out of all changes to finalizes network-wide reconvergence.
lastChangeTimestamp = max(convergenceTimes)

# Determine reconvergence time
reconvergenceTime = lastChangeTimestamp - startTimestamp

print(f"\nDown/Start time: {startTimeFormatted}")
print(f"Reconvergence time: {reconvergenceTime} milliseconds")


# %% [markdown]
# ## <span style="color: #034694"><b>Control Overhead & Blast Radius</b></span>

# %%
def parseTimestamp(line):
    '''
    Get the time of the failure message.
    '''
    return int(line.split(" ")[6].replace(",",""))

def parseOverhead(line, timestamp):
    '''
    Get the size of the failure message.
    '''
    overhead = int(line.split("=")[1]) if timestamp < testStopTime else 0

    return overhead

def getOverhead(logFile):
    with open(logFile) as file:
        logEntry = file.readline()
        size = 0
    
        while logEntry:
            if UPDATE_LOG_STATEMENT in logEntry:
                time = parseTimestamp(logEntry)
                size += parseOverhead(file.readline(), time)
    
            logEntry = file.readline()

    return size

# Control Overhead values
totalOverhead = 0

# Blast Radius values
totalNodeCount = 0
effectedNodeCount = 0

for logFile, nodeName in getResultsFile("convergence", includeNodeName=True):
    if(MTP_LOG_FILE_NAME in logFile):
        nodeOverhead = getOverhead(logFile)

        # Blast radius value updates
        totalNodeCount += 1
        if(nodeOverhead > 0 or nodeName in failedNodes):
            effectedNodeCount += 1

        # Add node's overhead to total overhead
        totalOverhead += nodeOverhead
        

# Calculate blast radius as the fraction of total nodes that received updates
blastRadius = (effectedNodeCount/totalNodeCount) * 100

# Print results
print(f"Overhead: {totalOverhead} bytes")
print(f"\nBlast radius: {blastRadius:.2f}% of nodes received VID failure information.")
print(f"\tNodes receiving updated information: {effectedNodeCount}\n\tTotal nodes: {totalNodeCount}")
