#!/usr/bin/env python3
#
# Copyright (C) 2017-2020 VyOS maintainers and contributors
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

import os

from sys import exit

from vyos.config import Config
from vyos import ConfigError
from vyos.util import call
from vyos.template import render
from vyos import airbag
from vyos.configdiff import get_config_diff
airbag.enable()

config_file = r'/tmp/isis.frr'

default_config_data = {
    'interface':  ''
}

def get_config():
    conf = Config()
    base = ['protocols', 'isis']
    isis = conf.get_config_dict(base, key_mangling=('-', '_'))
    diff_cfg = conf.get_config_dict(base, effective=True, key_mangling=('-', '_'))
    if not conf.exists(base):
        return None

    #from pprint import pprint
    #pprint(isis)

    return isis


def verify(isis):
    # bail out early - looks like removal from running config
    if not isis:
        return None

    from pprint import pprint
    pprint(isis)

    for proc_id, foo_config in isis['isis'].items():

        # If more then one isis process is defined (Frr only supports one)
        # http://docs.frrouting.org/en/latest/isisd.html#isis-router
        if len(isis['isis']) > 1:
            raise ConfigError('Only one isis process can be definded')

        # If network entity title (net) not defined
        if not "net" in  foo_config:
          raise ConfigError('Define net format iso is mandatory in \"isis {} net"!'.format(proc_id))

        # If interface not set
        if not "interface" in  foo_config:
          raise ConfigError('Define interface is mandatory in \"isis {} interface"!'.format(proc_id))

        # If md5 and plaintext-password set at the same time
        if 'area_password' in foo_config:
            if "md5" in foo_config['area_password'] and "plaintext_password" in foo_config['area_password']:
                raise ConfigError('Only one password type should be used in \"isis {} area-password"!'.format(proc_id))

        # If one param from deley set, but not set others
        if 'spf_delay_ietf' in foo_config:
            required_timers = ['holddown', 'init_delay', 'long_delay', 'short_delay', 'time_to_learn']
            exist_timers = []
            for elm_timer in required_timers:
                if elm_timer in foo_config['spf_delay_ietf']:
                    exist_timers.append(elm_timer)

            exist_timers = set(required_timers).difference(set(exist_timers))
            if len(exist_timers) > 0:
                raise ConfigError('All types of delay must be specified: ' + ', '.join(exist_timers).replace('_', '-'))

        # If Redistribute set, but level don't set
        if 'redistribute' in foo_config:
            proc_level = foo_config.get('level','').replace('-','_')
            for proto, proto_config in foo_config.get('redistribute', {}).get('ipv4', {}).items():
                if 'level_1' not in proto_config and 'level_2' not in proto_config:
                    raise ConfigError('Redistribute level-1 or level-2 should be specified in \"protocols isis {} redistribute ipv4 {}\"'.format(proc_id, proto))
            for redistribute_level in proto_config.keys():
                if proc_level and proc_level != 'level_1_2' and proc_level != redistribute_level:
                    raise ConfigError('\"protocols isis {0} redistribute ipv4 {2} {3}\" cannot be used with \"protocols isis {0} level {1}\"'.format(proc_id, proc_level, proto, redistribute_level))

    return None

def generate(isis):
    if not isis:
        return None

    render(config_file, 'frr/isis.frr.tmpl', isis)
    return None

def apply(isis):
    if isis is None:
        return None

    if os.path.exists(config_file):
        call(f'vtysh -d isisd -f {config_file}')
#        os.remove(config_file)
    else:
        print("File {0} not found".format(config_file))

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
