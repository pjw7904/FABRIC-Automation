log syslog informational
!
router bgp ${bgp_asn}
% for neighbor in neighbors:
 neighbor ${neighbor["ip"]} remote-as ${neighbor["asn"]}
% endfor
 !
% if networks:
 address-family ipv4 unicast
% for network in networks:
  network ${network}
% endfor
 exit-address-family
% endif
exit
!