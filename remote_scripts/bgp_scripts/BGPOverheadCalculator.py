'''
Analyze BGP packet captures (pcap) and determine the overhead resulting from those messages.
Author: Peter Willis (pjw7904@rit.edu)
'''
from scapy.all import *
from scapy.contrib.bgp import * # Need a specific import for BGP-related classes and headers

# Initialize values
BGPConf.use_2_bytes_asn = False # Set 4-byte ASN field, as that is what the FRR implementation uses.

UPDATE_HEADER = "BGPUpdate" # Look specifically for the BGP UPDATE header within the packets.
IP_HEADER = "IP" # IPv4 header name.
overhead = 0 # Overhead is defined as any layer 3+ data sent (i.e., the total length of the IP + TCP + BGP headers)

# Read the capture file and load the frames into the packets structure
packets = rdpcap("bgp_update_only.pcap")

# Iterate through the frames
for packet in packets:
	# For each packet that has the BGP UPDATE header and contains withdrawn routes, add to the overhead by the total packet size (IP length field)
	if(packet.haslayer(UPDATE_HEADER) and packet[UPDATE_HEADER].withdrawn_routes_len > 0):
		overhead += packet[IP_HEADER].len

# Write overhead to file
with open("overhead.log", "w") as logFile:
	logFile.write(str(overhead))