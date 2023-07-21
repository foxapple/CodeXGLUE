# Copyright Hybrid Logic Ltd.
# Copyright 2015 EMC Corporation
# See LICENSE file for details.

"""
EMC Test helpers for ``flocker.node.agents``.
"""

import os
import yaml
import socket
from uuid import uuid4

from twisted.trial.unittest import SkipTest

from emc_xtremio_flocker_plugin.emc_xtremio_blockdevice import (
    EMCXtremIOBlockDeviceAPI,
    ArrayConfiguration
)


def xio_client_from_environment():
    """
    Create EMC XTremIO XMS connection by picking up parameters
    from environment

    :returns:Arrayconfiguration Object
    """
    config_file_path = os.environ.get('XMS_CONFIG_FILE')
    if config_file_path is not None:
        config_file = open(config_file_path)
    else:
        raise SkipTest(
            'Supply the path to a EMC XtremIO config file '
            'using the XMS_CONFIG_FILE environment variable. '
            'See: '
            'https://docs.clusterhq.com/en/latest/gettinginvolved/acceptance-testing.html '  # noqa
            'for details of the expected format.'
        )
    config = yaml.load(config_file.read())
    xio_config = config['XIO']
    xms_username = xio_config['XMS_USER']
    xms_password = xio_config['XMS_PASS']
    xms_ip = xio_config['XMS_IP']

    return ArrayConfiguration(xms_username, xms_password, xms_ip)


def detach_destroy_volumes(api):
    """
    Detach and destroy all volumes known to this API.
    :param : api object
    """
    volumes = api.list_volumes()

    for volume in volumes:
        if volume.attached_to is not None:
            api.detach_volume(volume.blockdevice_id)
        api.destroy_volume(volume.blockdevice_id)


def destroy_volume_folder(api):
    """
    Destroy all volumes folders
    :param : api object
    """
    api.destroy_volume_folder()


def tidy_xio_client_for_test(test_case):
    """
    Return a ``EMCXtremIO Client`and register a ``test_case``
    cleanup callback to remove any volumes that are created during each test.
    :param test_case object
    """
    config = xio_client_from_environment()
    xio = EMCXtremIOBlockDeviceAPI(
        cluster_id=unicode(uuid4()),
        configuration=config,
        compute_instance_id=unicode(socket.gethostname()),
        allocation_unit=None)
    test_case.addCleanup(destroy_volume_folder, xio)
    test_case.addCleanup(detach_destroy_volumes, xio)

    return xio
