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
# # Experimenting with the <span style="color: #de4815"><b>Border Gateway Protocol (BGP)</b></span> For Data Center Networks
#
# ## <span style="color: #de4815"><b>Overview</b></span>
#
# A suite of automation tools to build a single-site FABRIC Slice that mirrors the setup of a BGP-based modern data center network for experimentation. The topology built is a traditional folded-Clos setup with a 1:1 oversubscription ratio, resulting in a rearrangably nonblocking network. Users will input information about the folded-Clos setup (the number of tiers and the ports-per-BGP-node) and a custom library will determine the appropriate configuration necessary for both the FABRIC infrastructure and the BGP configuration. The figure below illistrates a very high-level overview of this system:
#
# <center>
#     <div>
#         <img src="../figs/bgp_clos_diagram.png" width="650"/>
#     </div>
# </center>
#
# The [Free Range Routing (FRR)](https://docs.frrouting.org/en/latest/bgp.html) implementation of BGP is utilized.
#
# ## <span style="color: #de4815"><b>Usage</b></span>
#
# The following steps (via the linked books) should be followed to test BGP on a DCN (folded-Clos) topology. Clicking on each highlighed step will bring you to the associated Jupyter book.
#
# 1. [Build a BGP-DCN folded-Clos Topology](./BGP_ClosBuilder.ipynb): This will get you configured with a FABRIC slice containing the necessary BGP-DCN configuration. Nodes are available to SSH into and the configuration can be studied, along with any other manual changes to the topology or configuration desired.
#
# 2. [Run a reconvergence experiement](./BGP_Test.ipynb): A provided interface will be disabled and logs related to BGP reconverged will be collected.
#
# 3. [Analyze reconvergence logs against pre-defined metrics](./BGP_Analysis.ipynb): The logs collected from the reconvergence experiment can be analyzed for results based on the metrics reconvergence time, control overhead, and blast radius.
#
# If you want a centralized location to collect information outside of the reconvergence experiment system, use the [BGP Info book](./BGP_Info.ipynb)
#
# ## <span style="color: #de4815"><b>RFC 7938 Compliance</b></span>
#
# | RFC 7938 Section Number | Compliant Functionality                                                                                                                             |   |   |   |
# |-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|---|---|---|
# | 5.2.1                   | E-BGP single-hop sessions, no multi-hop or loopback sessions                                                                                        |   |   |   |
# | 5.2.2                   | A single ASN is allocated to all of the Clos topology's top-tier devices, a single ASN for all pod spines, and individual ASN’s for all leaf nodes. |   |   |   |
# | 5.2.3                   | Do not advertise any of the point-to-point (switch-to-switch) links into BGP. Only advertise server subnets.                                        |   |   |   |
# | 5.2.3                   | No route summarization for server subnets.                                                                                                          |   |   |   |
# | 6.1                     | Basic ECMP is implemented in FRR-BGP.                                                                                                               |   |   |   |
