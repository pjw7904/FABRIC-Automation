# %% [markdown]
# # <span style="color: #034694"><b>MTP</b></span> Source Code Updates
# 
# If you wish to make changes to the MTP implementation source code, this book gives you the necessary options to do so.

# %% [markdown]
# ## <span style="color: #034694"><b>Topology Information</b></span>
# 
# | Variable | Use |
# | --- | --- |
# | SLICE_NAME    | Name of the slice you want to access and observe |
# | NETWORK_NODE_PREFIXES    | The naming prefix(es) for MTP-speaking nodes |
# | CODE_DIRECTORY | The full path to your MTP source code directory |

# %%
SLICE_NAME = "update_testing"
NETWORK_NODE_PREFIXES = "T,S,L"
CODE_DIRECTORY = "/home/fabric/work/custom/CMTP"

# %% [markdown]
# ## <span style="color: #034694"><b>Access Slice Resources</b></span>
# 
# The FabOrchestrator class is used to grab information. This is a class that wraps around the underlying FabLib to make certain actions easier to run.

# %%
# Get acccess to FabUtils in the local_books dir first
import sys
sys.path.append('..')

# Then proceed with the rest of the imports (including FabUtils)
from FabUtils import FabOrchestrator

try:
    manager = FabOrchestrator(SLICE_NAME)
    
except Exception as e:
    print(f"Exception: {e}")

# %% [markdown]
# ## <span style="color: #034694"><b>Modify Code</b></span>
# 
# <b>WARNING</b>: Be careful that any change from the initial norm may break the functionality of the protocol.
# 
# The source code for your MTP implementation should already be downloaded somewhere on the FABRIC JupyterHub envionrment. 

# %%
# Uploading the MTP directory
manager.uploadDirectoryParallel(CODE_DIRECTORY, prefixList=NETWORK_NODE_PREFIXES)

# %%
# Compile the code
outputConfigCommand = 'cd ~/CMTP/SRC && gcc *.c -o MTPstart'
manager.executeCommandsParallel(outputConfigCommand, prefixList=NETWORK_NODE_PREFIXES)


