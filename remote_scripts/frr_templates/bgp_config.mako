sudo vtysh -c "conf t" -c "router bgp ${bgp_as}"

% for neighbor in neighbors:
sudo vtysh -c "conf t" -c "router bgp ${bgp_as}" -c "neighbor ${neighbor["as"]} remote-as ${neighbor["ip"]}"
% endfor

% if networks:
% for network in networks:
sudo vtysh -c "conf t" -c "router bgp ${bgp_as}" -c "address-family ipv4 unicast" -c "network ${network}"
% endfor
% endif