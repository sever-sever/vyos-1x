#!/usr/bin/env python3
#
# Copyright (C) 2021 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sys import exit

from vyos.config import Config
from vyos.configdict import get_interface_dict
from vyos.configdict import leaf_node_changed
from vyos.configverify import verify_address
from vyos.configverify import verify_bridge_delete
from vyos.util import call
from vyos.ifconfig import VETHIf
from vyos import ConfigError
from pprint import pprint

from vyos import airbag
airbag.enable()

def get_config(config=None):
    """
    Retrive CLI config as dictionary. Dictionary can never be empty, as at
    least the interface name will be added or a deleted flag
    """
    if config:
        conf = config
    else:
        conf = Config()
    base = ['interfaces', 'virtual-ethernet']
    veth = get_interface_dict(conf, base)

    # To delete a vethX interface we need the current netns
    if 'deleted' in veth:
        tmp = leaf_node_changed(conf, ['netns'])
        if tmp:
            # leaf_node_changed() returns a list
            veth.update({'netns': tmp[0]})

        # Maybe it doesn't needed. Need to check
        #tmp = leaf_node_changed(conf, ['peer'])
        #veth.update({'peer': tmp[0]})

    pprint(veth)
    return veth

def verify(veth):
    if 'deleted' in veth:
        verify_bridge_delete(veth)
        return None

    verify_address(veth)

    return None

def generate(veth):
    return None

def apply(veth):
    if 'deleted' in veth:
        # delete interface
        print('DEBUG Deleted:', veth)
        if 'netns' in veth:
            # Interface vethX attached to namespace
            # Delete link from netns
            print('ip -netns {netns} link del dev {ifname}'.format(**veth))
            call('ip -netns {netns} link del dev {ifname}'.format(**veth))
        else:
            # Interface vethX not attached to any namespace
            print('ip link del dev {ifname}'.format(**veth))
            call('ip link del dev {ifname}'.format(**veth))

        #exit(1)
        #VETHIf(veth['ifname']).remove()
        return None

    # Attach interface vethX to netns
    print('DEBUG: ', veth)
    if 'ifname' in veth:
        ve_ifname = veth['ifname']
    if 'netns' in veth:
        ve_netns = veth['netns']

    if {'ifname', 'netns'} <= set(veth):
        p = VETHIf(**veth)
        p.update(veth)
        print('DEBUG add: ip link add {ifname} type veth peer name {peer}'.format(**veth))
        print('DEBUG set: ip link set {ifname} netns {netns}'.format(**veth))
        call(f'ip link set {ve_ifname} netns {ve_netns}')
    elif 'peer' in veth:
        p = VETHIf(**veth)
        p.update(veth)
    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
