# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""High-level interface for listing installed handles

"""

__docformat__ = 'restructuredtext'

from os.path import join as opj, abspath

from .base import Interface
from datalad.support.param import Parameter
from datalad.support.constraints import EnsureStr
from datalad.support.collectionrepo import CollectionRepo
from datalad.support.collection_backends import CollectionRepoBackend
from datalad.support.handle_backends import CollectionRepoHandleBackend
from datalad.support.handle import Handle
from datalad.cmdline.helpers import get_datalad_master


class ListHandles(Interface):
    """List all locally installed or remote available handles."""

    _params_ = dict(
        remote=Parameter(
            args=("-r", "--remote"),
            action="store_true",
            doc="""Flag if to list remote handles (not local)"""),
    )

    def __call__(self, remote=False):
        """
        Parameters
        ----------
        remote: bool
            If True, list handles from registered remote collections only.
            Otherwise list locally installed handles instead.

        Returns
        -------
        list of Handle
        """

        local_master = get_datalad_master()
        handle_list = list()
        if remote:
            for remote_branch in local_master.git_get_remote_branches():
                if not remote_branch.endswith('/master'): # for now only those
                    continue
                for h in CollectionRepoBackend(local_master,
                                               branch=remote_branch):
                    handle_list.append(
                        CollectionRepoHandleBackend(local_master, key=h,
                                                    branch=remote_branch))
                    remote_name = '/'.join(remote_branch.split('/')[:-1])
                    print("%s/%s" % (remote_name, h))
        else:
            for handle in local_master.get_handle_list():
                handle_list.append(
                    CollectionRepoHandleBackend(local_master, handle))
                print(handle)

        if not self.cmdline:
            return handle_list

