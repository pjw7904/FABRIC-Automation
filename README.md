# FABRIC-Automation
A collection of scripts to help in the installation, configuration, and testing of experiments on the FABRIC testbed

## Installation

All required Python packages are already included on your FABRIC Testbed Jupyter Notebook provided by their JupyterHub. Simply clone or download this project from your Jupyter envionrment and you are ready to go.

Because of the ephameral nature of the remote Jupyter server, you should not extend this work with Python packages that would require an installation, as the JupyterHub will wipe your installed packages after a period of time (a day or so). 

FABRIC has done a good job of providing commonly-used third party packages, such as NetworkX or NumPy, so you should be able to find an exisiting alternative to a library you really want to include.

## Usage

| Directory | Description |
| ----------- | ----------- |
| figs | Images that are included in books should be saved here. |
| graphs | GraphML files should be saved here. Look at the existing files to learn the syntax. |
| local_books | The Jupyter notebooks to be run on the FABRIC Jupyter enviornment to build networks. Anything involving Slice creation, modification, and any and all calls to the FabLib or MFLib API should be included in books located here. |
| remote_scripts | Any scripts (Bash, Python, etc.) that would be uploaded to FABRIC nodes to be run locally. |

Slice creation is typically done by first writing a GraphML file (either manually or via a script), placing it in the graphs directory, and then running a Slice builder book in local_books to complete initial configuration. Beyond creating the network, builder books usually include setting IPv4 addressing, installing necessary packages, etc.

From there, the protocol being tested and the type of experiment being run will determine what book(s) to run next. Alternatively, you can remotely access the nodes and manually input commands.

A wrapper around the FabLib API, the FabUtils class, is included in local_books to make common tasks run by our research team easier to code.

## Configuration

There is no global configuration for the books included. Each book will include a section where important information will need to be set prior to running the rest of the cells. Sometimes, no information will be required other than how to access the slice (usually the slice name).

For example, the generic FRR builder book will require the following information:

```python
SLICE_NAME = "frr_test"
SITE_NAME = "NEWY"
GRAPH_PATH = "/home/fabric/work/custom/FABRIC-Automation/graphs/linear.graphml"
FRR_SCRIPT = "init_bgp.sh"
HAS_CLIENTS = True
CLIENT_PREFIX = "C"
MEAS_ADD = False
```

The meaning and signifigance of each variable is explained in a text cell prior to inputting this information.