# Copyright 2021 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

from vyos.ifconfig.interface import Interface

@Interface.register
class VETHIf(Interface):
    """
    Virtual Ethernet veth interface
    """
    iftype = 'veth'
    definition = {
        **Interface.definition,
        **{
            'section': 'virtual-ethernet',
            'prefixes': ['veth', ],
            'bridgeable': True,
        },
    }

    def _create(self):
        cmd = 'ip link add {ifname} type veth peer name {peer}'
        self._cmd(cmd.format(**self.config))
        self.set_admin_state('up')

    def remove(self):
        if self.exists(self.ifname):
            if {'peer', 'netns'} <= set(self.config):
                cmd = 'ip -netns {netns} link del dev {ifname}'
                self._cmd(cmd.format(**self.config))
