#!/usr/bin/env python3
#
# Copyright (C) 2019-2020 VyOS maintainers and contributors
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

from vyos.config import Config
from vyos import ConfigError
from vyos.util import call
from vyos.template import render

from vyos import airbag
airbag.enable()

config_file = r'/tmp/ldpd.frr'

def sysctl(name, value):
    call('sysctl -wq {}={}'.format(name, value))

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    mpls_conf = {
        'router_id'  : None,
        'mpls_ldp'   : False,
        'old_ldp'    : {
                'interfaces'          : [],
                'neighbors'           : {},
                'param_cisco_tlv'     : False,
                'param_transp_pref_ipv4': False,
                'd_transp_ipv4'       : None,
                'd_transp_ipv6'       : None,
                'hello_holdtime'      : None,
                'hello_interval'      : None,
                'ses_ipv4_hold'       : None,
                'ses_ipv6_hold'       : None,
                'export_ipv4_exp'     : False,
                'export_ipv6_exp'     : False

        },
        'ldp'        : {
                'interfaces'          : [],
                'neighbors'           : {},
                'param_cisco_tlv'     : False,
                'param_transp_pref_ipv4': False,
                'd_transp_ipv4'       : None,
                'd_transp_ipv6'       : None,
                'hello_holdtime'      : None,
                'hello_interval'      : None,
                'ses_ipv4_hold'       : None,
                'ses_ipv6_hold'       : None,
                'export_ipv4_exp'     : False,
                'export_ipv6_exp'     : False

        }
    }
    if not (conf.exists('protocols mpls') or conf.exists_effective('protocols mpls')):
        return None

    if conf.exists('protocols mpls ldp'):
        mpls_conf['mpls_ldp'] = True

    conf.set_level('protocols mpls ldp')

    # Get router-id
    if conf.exists_effective('router-id'):
        mpls_conf['old_router_id'] = conf.return_effective_value('router-id')
    if conf.exists('router-id'):
        mpls_conf['router_id'] = conf.return_value('router-id')

    # Get hello holdtime
    if conf.exists_effective('discovery hello-holdtime'):
        mpls_conf['old_ldp']['hello_holdtime'] = conf.return_effective_value('discovery hello-holdtime')

    if conf.exists('discovery hello-holdtime'):
        mpls_conf['ldp']['hello_holdtime'] = conf.return_value('discovery hello-holdtime')

    # Get hello interval
    if conf.exists_effective('discovery hello-interval'):
        mpls_conf['old_ldp']['hello_interval'] = conf.return_effective_value('discovery hello-interval')

    if conf.exists('discovery hello-interval'):
        mpls_conf['ldp']['hello_interval'] = conf.return_value('discovery hello-interval')

    # Get session-ipv4-holdtime
    if conf.exists_effective('discovery session-ipv4-holdtime'):
        mpls_conf['old_ldp']['ses_ipv4_hold'] = conf.return_effective_value('discovery session-ipv4-holdtime')

    if conf.exists('discovery session-ipv4-holdtime'):
        mpls_conf['ldp']['ses_ipv4_hold'] = conf.return_value('discovery session-ipv4-holdtime')

    # Get session-ipv6-holdtime
    if conf.exists_effective('discovery session-ipv6-holdtime'):
        mpls_conf['old_ldp']['ses_ipv6_hold'] = conf.return_effective_value('discovery session-ipv6-holdtime')

    if conf.exists('discovery session-ipv6-holdtime'):
        mpls_conf['ldp']['ses_ipv6_hold'] = conf.return_value('discovery session-ipv6-holdtime')

    # Get discovery transport-ipv4-address
    if conf.exists_effective('discovery transport-ipv4-address'):
        mpls_conf['old_ldp']['d_transp_ipv4'] = conf.return_effective_value('discovery transport-ipv4-address')

    if conf.exists('discovery transport-ipv4-address'):
        mpls_conf['ldp']['d_transp_ipv4'] = conf.return_value('discovery transport-ipv4-address')

    # Get discovery transport-ipv6-address
    if conf.exists_effective('discovery transport-ipv6-address'):
        mpls_conf['old_ldp']['d_transp_ipv6'] = conf.return_effective_value('discovery transport-ipv6-address')

    if conf.exists('discovery transport-ipv6-address'):
        mpls_conf['ldp']['d_transp_ipv6'] = conf.return_value('discovery transport-ipv6-address')

    # Get export ipv4 explicit-null
    if conf.exists_effective('export ipv4 explicit-null'):
        mpls_conf['old_ldp']['export_ipv4_exp'] = True

    if conf.exists('export ipv4 explicit-null'):
        mpls_conf['ldp']['export_ipv4_exp'] = True

    # Get export ipv6 explicit-null
    if conf.exists_effective('export ipv6 explicit-null'):
        mpls_conf['old_ldp']['export_ipv6_exp'] = True

    if conf.exists('export ipv6 explicit-null'):
        mpls_conf['ldp']['export_ipv6_exp'] = True

    # Get interfaces
    if conf.exists_effective('interface'):
        mpls_conf['old_ldp']['interfaces'] = conf.return_effective_values('interface')

    if conf.exists('interface'):
        mpls_conf['ldp']['interfaces'] = conf.return_values('interface')

    # Get neighbors
    for neighbor in conf.list_effective_nodes('neighbor'):
        mpls_conf['old_ldp']['neighbors'].update({
            neighbor : {
                'password' : conf.return_effective_value('neighbor {0} password'.format(neighbor))
            }
        })

    for neighbor in conf.list_nodes('neighbor'):
        mpls_conf['ldp']['neighbors'].update({
            neighbor : {
                'password' : conf.return_value('neighbor {0} password'.format(neighbor))
            }
        })

    # Get parameters cisco-interop-tlv
    if conf.exists_effective('parameters cisco-interop-tlv'):
        mpls_conf['old_ldp']['param_cisco_tlv'] = True

    if conf.exists('parameters cisco-interop-tlv'):
        mpls_conf['ldp']['param_cisco_tlv'] = True

    # Get parameters transport-prefer-ipv4
    if conf.exists_effective('parameters transport-prefer-ipv4'):
        mpls_conf['old_ldp']['param_transp_pref_ipv4'] = True

    if conf.exists('parameters transport-prefer-ipv4'):
        mpls_conf['ldp']['param_transp_pref_ipv4'] = True

    return mpls_conf

def operate_mpls_on_intfc(interfaces, action):
    rp_filter = 0
    if action == 1:
        rp_filter = 2
    for iface in interfaces:
        sysctl('net.mpls.conf.{0}.input'.format(iface), action)
        # Operate rp filter
        sysctl('net.ipv4.conf.{0}.rp_filter'.format(iface), rp_filter)

def verify(mpls):
    if mpls is None:
        return None

    if mpls['mpls_ldp']:
        # Requre router-id
        if not mpls['router_id']:
            raise ConfigError(f"MPLS ldp router-id is mandatory!")

        # Requre discovery transport-address
        if not mpls['ldp']['d_transp_ipv4'] and not mpls['ldp']['d_transp_ipv6']:
            raise ConfigError(f"MPLS ldp discovery transport address is mandatory!")

        # Requre interface
        if not mpls['ldp']['interfaces']:
            raise ConfigError(f"MPLS ldp interface is mandatory!")

def generate(mpls):
    if mpls is None:
        return None

    render(config_file, 'frr/ldpd.frr.tmpl', mpls)
    return None

def apply(mpls):
    if mpls is None:
        return None

     # Set number of entries in the platform label table
    if mpls['mpls_ldp']:
        sysctl('net.mpls.platform_labels', '1048575')
    else:
        sysctl('net.mpls.platform_labels', '0')

    # Do not copy IP TTL to MPLS header
    sysctl('net.mpls.ip_ttl_propagate', '0')

    # Allow mpls on interfaces
    operate_mpls_on_intfc(mpls['ldp']['interfaces'], 1)

    # Disable mpls on deleted interfaces
    diactive_ifaces = set(mpls['old_ldp']['interfaces']).difference(mpls['ldp']['interfaces'])
    operate_mpls_on_intfc(diactive_ifaces, 0)

    if os.path.exists(config_file):
        call(f'vtysh -d ldpd -f {config_file}')
        os.remove(config_file)

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
