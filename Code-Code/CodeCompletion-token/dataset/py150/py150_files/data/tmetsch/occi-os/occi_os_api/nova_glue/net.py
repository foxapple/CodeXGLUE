# coding=utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Copyright (c) 2012, Intel Performance Learning Solutions Ltd.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Network related 'glue' :-)
"""

import logging

from nova import compute

from occi_os_api.nova_glue import vm

# Connect to nova :-)

NETWORK_API = compute.API().network_api


LOG = logging.getLogger(__name__)


def get_network_details(uid, context):
    """
    Extracts the VMs network adapter information.

    uid -- Id of the VM.
    context -- The os context.
    """
    vm_instance = vm.get_vm(uid, context)

    result = {'public': [], 'admin': []}
    try:
        net_info = NETWORK_API.get_instance_nw_info(context, vm_instance)[0]
    except IndexError:
        LOG.warn('Unable to retrieve network information - this is because '
                 'of OpenStack!!')
        return result
    gw = net_info['network']['subnets'][0]['gateway']['address']
    mac = net_info['address']

    if len(net_info['network']['subnets'][0]['ips']) == 0:
        tmp = {'floating_ips': [], 'address': '0.0.0.0'}
    else:
        tmp = net_info['network']['subnets'][0]['ips'][0]
    for item in tmp['floating_ips']:
        result['public'].append({'interface': 'eth0',
                                 'mac': 'aa:bb:cc:dd:ee:ff',
                                 'state': 'active',
                                 'address': item['address'],
                                 'gateway': '0.0.0.0',
                                 'allocation': 'static'})
    result['admin'].append({'interface': 'eth0',
                            'mac': mac,
                            'state': 'active',
                            'address': tmp['address'],
                            'gateway': gw,
                            'allocation': 'static'})

    return result


def add_floating_ip(uid, pool_name, context):
    """
    Adds an ip to an VM instance.

    uid -- id of the VM.
    pool_name -- name of the pool
    context -- The os context.
    """
    vm_instance = vm.get_vm(uid, context)

    # FIXME: currently quantum driver has a notimplemented here :-(
    # fixed_ips = NETWORK_API.get_fixed_ip(uid, context)
    # NOTE(aloga): nova-network is still suported in Grizzly, so we
    # should not drop support for it.
    tmp = NETWORK_API.get_instance_nw_info(context, vm_instance)[0]
    fixed_ip = tmp.fixed_ips()[0]['address']

    float_address = NETWORK_API.allocate_floating_ip(context, pool_name)

    try:
        address = fixed_ip
        NETWORK_API.associate_floating_ip(context, vm_instance,
                                          float_address, address)
    except Exception as e:
        raise AttributeError(e.message)
    return float_address


def remove_floating_ip(uid, address, context):
    """
    Remove a given address from an VM instance.

    uid -- Id of the VM.
    address -- The ip address.
    context -- The os context.
    """
    vm_instance = vm.get_vm(uid, context)

    try:
        NETWORK_API.disassociate_floating_ip(context, vm_instance, address)
        NETWORK_API.release_floating_ip(context, address)
    except Exception as e:
        raise AttributeError(e.message)
