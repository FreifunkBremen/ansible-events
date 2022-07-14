#!/bin/env python3

from json import dumps as jsondumps

import ipaddress
import re
import math

# {
#   "bauwagen": {
#      "_meta": {
#         "hostvars": {
#           "a": {
#             "ansible_ssh_host": ""
#            }
#         }
#      },
#     "hosts": [
#       "a"
#     ],
#   }
# }

class Inventory:

    def __init__(self,
            ipv6_subnet,
            radius=0.00001,

            radio24_channel_auto_enabled=False,
            radio24_channel_auto_list = [1, 
                # 2, 3, 4, 
                5, 
                # 6, 7, 8, 
                9, 
                # 10, 11, 12,
                13],

            radio5_channel_auto_enabled=False,
            radio5_channel_auto_list = [
                # 32, why?
                36,40,44,48,
                # dfs:
                # 50, 52, 56, 60, 64, 68, 96, 100,...
                149,
                # 151, why?
                153, 
                # 155, why?
                157, 
                # 159, why? or channel 11 ?
                161, 165, 169, 173
                ],

            **kwargs):
        self._groups = {}

        self._ipv6_subnet = ipaddress.ip_network(ipv6_subnet, strict=False)

        self._radius = radius

        self._radio24_channel_auto_enabled = radio24_channel_auto_enabled
        self._radio24_channel_auto_list = radio24_channel_auto_list

        self._radio5_channel_auto_enabled = radio5_channel_auto_enabled
        self._radio5_channel_auto_list = radio5_channel_auto_list
        
        self._inventory_vars = kwargs

    def newGroup(self, name, **kwargs):
        index = len(self._groups)
        group = Group(self, index, name, **kwargs)
        self._groups[name] = group
        return group

    def calc_ip_by_node_id(self, node_id):
        # https://gist.github.com/wido/f5e32576bb57b5cc6f934e177a37a0d3

        # http://tools.ietf.org/html/rfc4291#section-2.5.1
        eui64 = node_id.lower()
        eui64 = eui64[0:6] + 'fffe' + eui64[6:]
        eui64 = hex(int(eui64[0:2], 16) ^ 2)[2:].zfill(2) + eui64[2:]

        return str(self._ipv6_subnet.network_address) + ':'.join(re.findall(r'.{4}', eui64))

    def getChannel(self, band=24, group_i = 0, host_i = 0):
        # get Radio specifical variables
        channel_default = None 
        channel_auto_enabled = self._radio24_channel_auto_enabled
        channel_auto_list = self._radio24_channel_auto_list
        if "radio24_channel" in self._inventory_vars:
            channel_default = self._inventory_vars["radio24_channel"]

        if band == 5:
          channel_auto_enabled = self._radio5_channel_auto_enabled
          channel_auto_list = self._radio5_channel_auto_list
          if "radio5_channel" in self._inventory_vars:
            channel_default = self._inventory_vars["radio5_channel"]


        ##
        # Generic Part
        #
        # TODO Intelligence to make somethink nice over all
        ##
        if not channel_auto_enabled:
            return channel_default

        channel_count = len(channel_auto_list)

        # channel_index = host_i % channel_count
        # if band == 5:
        channel_index = (group_i * 10 + host_i) % channel_count

        return channel_auto_list[channel_index]



    def data(self):
        data = {
            "_meta": {
                "hostvars": {}
            }
        }
        hosts_vars = {}

        for name, group in self._groups.items():
            hosts = []

            for (host, origin_hostvars) in group.hosts():
                hosts.append(host)
                # merge with inventory_vars
                hostvars = self._inventory_vars.copy()
                hostvars.update(origin_hostvars)
                # add host vars to meta
                data["_meta"]["hostvars"][host] = hostvars

            data[name] = {
                    "hosts": hosts,
            }
        return data

    def json_dump(self, **kwargs):
        return jsondumps(self.data(), **kwargs)

class Group:
    def __init__(self, inventory, index, name, ignore=False, geo_latitude=None,geo_longitude=None):
        self._inventory = inventory
        self._index = index
        self._name = name
        self._geo_latitude = geo_latitude
        self._geo_longitude = geo_longitude
        self._hosts = []
        self._ignore = ignore

    def hosts(self):
        if self._ignore:
            return []

        hosts = []

        hostCount = len(self._hosts)

        ignoreCount = 0

        for (enumI, (node_id, origin_data)) in enumerate(self._hosts):
            if "ignore" in origin_data and origin_data["ignore"]:
                ignoreCount+=1
                continue
            i = enumI-ignoreCount
            data = origin_data.copy()

            # calc ip address for SSH by node_id
            if not "ansible_ssh_host" in data:
                data["ansible_ssh_host"] = self._inventory.calc_ip_by_node_id(node_id)

            # node_name by group name
            if not "node_name" in data:
                data["node_name"] = f"{self._name}-{i+1}"

            # group name as owner
            if not "owner" in data:
                data["owner"] = self._name

            # calc geolocation by group 
            # TODO current just copy ...
            if self._geo_latitude is not None and self._geo_longitude is not None and \
              not "geo_latitude" in data and not "geo_longitude" in data:
                if hostCount > 1:
                  (lati, longi) = calc_geo(
                          x0=self._geo_latitude, 
                          y0=self._geo_longitude,
                          radius=self._inventory._radius,
                          i=i,
                          items=hostCount
                        )
                  data["geo_latitude"] = lati
                  data["geo_longitude"] = longi
                elif hostCount == 1:
                  data["geo_latitude"] = self._geo_latitude
                  data["geo_longitude"] = self._geo_longitude

            if not "radio24_channel" in data:
                channel = self._inventory.getChannel(band=24, group_i = self._index, host_i = i)
                if channel is not None:
                    data["radio24_channel"] = channel

            if not "radio5_channel" in data:
                channel = self._inventory.getChannel(band=5, group_i = self._index, host_i = i)
                if channel is not None:
                    data["radio5_channel"] = channel

            hosts.append((node_id, data))
        return hosts


    def addNode(self, node_id, **kwargs):
        self._hosts.append((node_id, kwargs))


def calc_geo(x0, y0, radius=0.0001,i=0, items=1):
    factor = 2*math.pi*(i+1)/items
    x = x0 + radius*math.cos(factor)
    y = y0 + radius*math.sin(factor)
    return (x, y)

if __name__ == "__main__":
    inv = Inventory(
        ##
        # default
        ##
        ipv6_subnet="fd00:42:100::/64",
        ##
        # generic extra vars to hostvars
        ##
        syslog_ip="fd00:42:100::10"
        #- syslog_port="1514"
    )
    # first / name required
    grp = inv.newGroup("Bauwagen",
        # "fallbacks" to calc
        geo_latitude=53.069581438,
        geo_longitude=8.818759033)

    grp.addNode("d46e0e28f8cd",
            # generic extra vars to hostvars
            syslog_ip="fd00:42:100::13"
    )
    grp.addNode("d46e0e366a3e")

    print(inv.json_dump())
