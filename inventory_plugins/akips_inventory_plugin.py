from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: akips_inventory_plugin
    plugin_type: inventory
    short_description: Returns Ansible inventory from akips network discovery tool
    description: Returns Ansible inventory from akips network discovery tool
    options:
      plugin:
          description: Name of the plugin
          required: true
          choices: ['akips_inventory_plugin']
      akips_username:
        description: username for connecting to akips api
        required: true
      akips_password:
        description: password for connecting to akips api
        required: true
      akips_host:
        description: hostname of the akips server
        required: true
'''

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError, AnsibleParserError
from pyakips3.akips_api import PyAkipsApi
import csv
import os
import sys

class InventoryModule(BaseInventoryPlugin):
    NAME = 'akips_inventory_plugin'

    def _build_inventory(self, akips_host, akips_user, akips_password):

        akips = PyAkipsApi(akips_host, akips_user, akips_password)

        skip_groups = ['Aruba-AP', 'Cisco-AP']
        
        all_devices = { item.devname : item for item in akips.get_device_snmp2_mibs() }
        all_devices_ip = { item.devname : item for item in akips.get_device_ipv4_addresses() }
        all_groups = list(akips.get_device_groups())

        # iterate through all the groups, if the group should not be skipped
        # get the members of the group and populate the json output
        # also update the _meta hostvars with the ansible_host (ip address) for the target device

        for group in all_groups:
            if not group in skip_groups:
                group_members = []
                devices = akips.get_device_group_members(group)
                for device in devices:
                    group_members.append(device)
                    hostvars.update({device : {'ansible_host': str(all_devices_ip[device].ipaddr)}})
                inventory_output.update({group : group_members})
                inventory_output['all']['children'].append(group)

        inventory_output.update({'_meta': {'hostvars': hostvars}})
        return inventory_output
            
    def verify_file(self, path):

        '''
        put any verification steps here
        '''

        return True
    
    def parse(self, inventory, loader, path, cache):
       '''Return dynamic inventory from source '''

       super(InventoryModule, self).parse(inventory, loader, path, cache)
    
       self._read_config_data(path)
       try:
           # Store the options from the YAML file
           self.plugin = self.get_option('plugin')
           self.akips_username = self.get_option('akips_username')
           self.akips_password = self.get_option('akips_password')
           self.akips_host = self.get_option('akips_host')
       except Exception as e:
           raise AnsibleParserError(
               'All correct options required: {}'.format(e))
       self._build_inventory(self, akips_host, akips_username, akips_password)
