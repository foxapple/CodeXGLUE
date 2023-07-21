##
# Copyright 2002-2012 Ilja Livenson, PDC KTH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##
import time
import re
from httplib import NOT_FOUND, OK, CREATED, NO_CONTENT, CONFLICT, FORBIDDEN, \
            UNAUTHORIZED

from twisted.python import log

import vcdm
from vcdm.server.cdmi.generic import get_parent
from vcdm.utils import check_path
from vcdm.authz import authorize


def read(avatar, requested_path, on_behalf=None):
    """ Read a specified container."""
    expected_fields = ['children', 'metadata', 'mtime']
    unique_request = re.match('/cdmi_objectid/\w+$', requested_path)
    if unique_request is not None:
        requested_uid = unique_request.group(0).split('/')[2]
        uid, vals = vcdm.env['ds'].find_by_uid(requested_uid, object_type='container',
                                            fields=expected_fields + ['fullpath'])
        fullpath = vals['fullpath']
    else:
        fullpath = requested_path
        uid, vals = vcdm.env['ds'].find_by_path(fullpath, object_type='container',
                                                fields=expected_fields)
    if uid is None:
        return (NOT_FOUND, None)
    else:
        # authorize call
        acls = vals['metadata'].get('cdmi_acl')
        if not authorize(avatar, fullpath, 'read_container', acls):
            return (UNAUTHORIZED, None)
        vals['uid'] = uid
        log.msg(type='accounting', avatar=avatar if not on_behalf else on_behalf,
                amount=1, acc_type='container_read')
        return (OK, vals)


def create_or_update(avatar, name, container_path, fullpath, metadata=None,
                     on_behalf=None):
    """Create or update a container."""
    log.msg("Container create/update: %s" % fullpath)

    parent_container = get_parent(fullpath)
    uid, vals = vcdm.env['ds'].find_by_path(fullpath, object_type='container',
                                            fields=['children',
                                                    'parent_container',
                                                    'owner'])
    vals['uid'] = uid
    # XXX: duplication of checks with blob (vcdm). Refactor.
    if uid is not None and parent_container != vals['parent_container']:
        log.err("Inconsistency! path: %s, parent_container in db: %s" % (fullpath, vals['parent_container']))
        return (FORBIDDEN, vals)

    # assert we can write to the defined path
    if not check_path(container_path):
        log.err("Writing to a container is not allowed. Container path: %s" %
                '/'.join(container_path))
        return (FORBIDDEN, vals)

    # authorize call, take parent permissions
    _, cvals = vcdm.env['ds'].find_by_path(parent_container,
                                           object_type='container',
                                           fields=['metadata'])
    acl = cvals['metadata'].get('cdmi_acl', {})
    if not authorize(avatar, parent_container, "write_container", acl):
        return (UNAUTHORIZED, vals)

    # add default acls
    if avatar is None:
            avatar = 'Anonymous'
    container_acl = metadata.get('cdmi_acl')
    if container_acl is None:
        metadata['cdmi_acl'] = acl  # append parent ACLs for a new folder
    metadata['cdmi_acl'].update({avatar: 'rwd'})  # and creator's ACLs

    # if uid is None, it shall create a new entry, update otherwise
    if uid is None:
        uid = vcdm.env['ds'].write({
                        'object': 'container',
                        'metadata': metadata,
                        'owner': avatar,
                        'fullpath': fullpath,
                        'name': name,
                        'parent_container': parent_container,
                        'children': {},
                        'ctime': str(time.time()),
                        'mtime': str(time.time())},
                        uid)
        vals['uid'] = uid
        # update the parent container as well, unless it's a top-level container
        if fullpath != '/':
            _append_child(parent_container, uid, name + "/")
        log.msg(type='accounting', avatar=avatar if not on_behalf else on_behalf,
                amount=1, acc_type='container_create')
        return (CREATED, vals)
    else:
        # update container
        # forbid rewrites of containers by other users
        if vals.get('owner') is not None and vals.get('owner') != avatar:
            return (UNAUTHORIZED, vals)
        uid = vcdm.env['ds'].write({
                        'metadata': metadata,
                        'mtime': str(time.time())},
                        uid)
        log.msg(type='accounting', avatar=avatar if not on_behalf else on_behalf,
                amount=1, acc_type='container_update')
        return (NO_CONTENT, vals)


def delete(avatar, fullpath, on_behalf=None):
    """ Delete a container."""
    log.msg("Deleting a container %s" % fullpath)
    uid, vals = vcdm.env['ds'].find_by_path(fullpath, object_type='container',
                                            fields=['children',
                                                    'parent_container',
                                                    'metadata'])
    if uid is None:
        return NOT_FOUND
    else:
        # authorize call
        acls = vals['metadata'].get('cdmi_acl', None)
        if not authorize(avatar, fullpath, "delete_container", acls):
            log.err("Authorization failed.")
            return UNAUTHORIZED
        # fail if we are deleting a non-empty container
        if len(vals['children']) != 0:
            log.err("Cannot delete non-empty container %s. Existing children: %s."
                    % (fullpath, vals['children']))
            # we do not allow deleting non-empty containers
            return CONFLICT
        vcdm.env['ds'].delete(uid)
        if fullpath != '/':
            _remove_child(vals['parent_container'], uid)
        ## XXX: delete all children?
        log.msg(type='accounting', avatar=avatar if not on_behalf else on_behalf,
                amount=1, acc_type='container_delete')
        return NO_CONTENT

####### Support functions dealing with container logic #########


def _append_child(container_path, child_uid, child_name):
    log.msg("Appending child %s:%s to a container %s" % (child_uid, child_name,
                                                        container_path))

    cuid, cvals = vcdm.env['ds'].find_by_path(container_path,
                                              object_type='container',
                                              fields=['children'])
    # append a new uid-pathname pair
    cvals['children'][unicode(child_uid)] = unicode(child_name)
    vcdm.env['ds'].write({
                    'children': cvals['children'],
                    'mtime': str(time.time())},
                    cuid)


def _remove_child(container_path, child_uid):
    log.msg("Removing child %s from a container %s" %
            (child_uid, container_path))
    cuid, cvals = vcdm.env['ds'].find_by_path(container_path,
                                              object_type='container',
                                              fields=['children'])
    del cvals['children'][child_uid]
    vcdm.env['ds'].write({
                    'children': cvals['children'],
                    'mtime': str(time.time())},
                    cuid)
