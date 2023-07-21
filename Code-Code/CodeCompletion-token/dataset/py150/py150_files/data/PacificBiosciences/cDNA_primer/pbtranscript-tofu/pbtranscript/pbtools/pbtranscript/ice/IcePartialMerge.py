#!/usr/bin/env python
###############################################################################
# Copyright (c) 2011-2013, Pacific Biosciences of California, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of Pacific Biosciences nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE.  THIS SOFTWARE IS PROVIDED BY PACIFIC BIOSCIENCES AND ITS
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL PACIFIC BIOSCIENCES OR
# ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###############################################################################

"""
Overview:
    pbtranscript cluster contains two main components:
    * (1) ICE (iterative clustering and error correction) to predict
      unpolished consensus isoforms.
    * (2) Polish, to use nfl reads and quiver to polish those predicted
      unpolished isoforms. Polish contains three steps:
      + (2.1) IceAllPartials (ice_partial.py all)
              Align and assign nfl reads to unpolished isoforms, and
              save results to a pickle file.
      + (2.2) IceQuiver (ice_quiver.py all)
              Call quiver to polish each isoform based on alignments
              created by mapping its associated fl and nfl reads to
              this isoform.
      + (2.3) IceQuiverPostprocess (ice_quiver.py postprocess)
              Collect and post process quiver results, and classify
              HQ/LQ isoforms.

    In order to handle subtasks by SMRTPipe instead of pbtranscript
    itself, we will refactor the polish phase including
    (2.1) (2.2) and (2.3).

    (2.1) IceAllPartials (ice_partial.py all) will be refactored to
      + (2.1.1) ice_partial.py split
                Split nfl reads into N chunks (N<=100).
      + (2.1.2) ice_partial.py i
                For each chunk i, align and assign its reads to unpolished
                isoforms and create a pickle file.
      + (2.1.3) ice_partial.py merge
                Merge pickles for all splitted chunks together to a
                big pickle.

    *** Here we are focusing on (2.1.3) ice_partial.py merge ***

Description:
    (2.1.3) ice_partial.py merge

    Assumption:
      * Phase (1) ICE is done and unpolished isoforms created.
      * ice_partial.py split has been called to split nfl reads into N chunks
      * ice_partial.py i has been applied to each chunk
      * we will collect and merge pickles for each chunk into a big pickle.

    Process:
        Given root_dir, and N, merge pickles of N chunks of nfl reads into
        a big pickle.

        The pikle file of the i-th chunk is at:
            root_dir/output/map_noFL/input.split_{0:02d}.fa.partial_uc.pickle

    Input:
      Positional:
        root_dir, an output directory for running pbtranscript cluster.
        N, the number of chunks of nfl reads.

    Output:
        Merge pickles of N nfl reads chunks into a big pickle at:
            root_dir/output/map_noFL/nfl.all.partial_uc.pickle,

    Hierarchy:
        pbtranscript = iceiterative

        pbtranscript --quiver = iceiterative + \
                                ice_polish.py

        ice_polish.py =  ice_make_fasta_fofn.py + \
                         ice_partial.py all + \
                         ice_quiver.py all

        ice_partial.py all = ice_partial.py split + \
                             ice_partial.py i + \
                             ice_partial.py merge

        (ice_partial.py one --> only apply ice_partial on a given input fasta)

        ice_quiver.py all = ice_quiver.py i + \
                            ice_quiver.py merge + \
                            ice_quiver.py postprocess

    Example:
        ice_partial.py merge root_dir N
"""

import logging
import os.path as op
from pbtools.pbtranscript.__init__ import get_version
from pbtools.pbtranscript.PBTranscriptOptions import \
    add_cluster_root_dir_as_positional_argument
from pbtools.pbtranscript.Utils import nfs_exists
from pbtools.pbtranscript.ice.IceFiles import IceFiles
from pbtools.pbtranscript.ice.IceUtils import combine_nfl_pickles


def add_ice_partial_merge_arguments(parser):
    """Add IcePartialmerge arguments."""
    parser = add_cluster_root_dir_as_positional_argument(parser)

    helpstr = "Non-full-length reads have been splitted into N chunks."
    parser.add_argument("N", help=helpstr, type=int)
    return parser


class IcePartialMerge(object):

    """IcePartialMerge"""

    # Define description of IcePartialMerge
    desc = "Merge pickles of N chunks of non-full-length reads into " + \
           "a big pickle file."

    prog = "ice_partial.py merge "  # used by cmd_str and ice_partial.py

    def __init__(self, root_dir, N):
        self.root_dir = root_dir
        self.N = int(N)

    def getVersion(self):
        """Return version string."""
        return get_version()

    def cmd_str(self):
        """Return a cmd string."""
        return self._cmd_str(root_dir=self.root_dir, N=self.N)

    def _cmd_str(self, root_dir, N):
        """Return a cmd string."""
        return self.prog + \
            "{d} ".format(d=root_dir) + \
            "{N} ".format(N=N)

    def validate_inputs(self):
        """Check inputs, return
        (splitted_pickles, out_pickle), where
        splitted_pickles are N pickles created by ice_partial.py i,
        and out_pickle is the final output pickle assigning all
        nfl reads to unpolished isoforms.
        """
        return self._validate_inputs(root_dir=self.root_dir,
                                    N=self.N)

    def _validate_inputs(self, root_dir, N):
        """
        Check inputs, return
        (splitted_pickles, out_pickle)
        """
        icef = IceFiles(prog_name="ice_partial_merge",
                        root_dir=root_dir, no_log_f=False)

        # root_dir/output/map_noFL/input.split_{0:02d}.fa.partial_uc.pickle
        splitted_pickles = [icef.nfl_pickle_i(i) for i in range(0, N)]
        # root_dir/output/map_noFL/input.split_{0:02d}.fa.partial_uc.pickle.DONE
        dones = [icef.nfl_done_i(i) for i in range(0, N)]

        # Check if inputs exist.
        errMsg = ""
        for done in dones:
            if not nfs_exists(done):
                errMsg = "DONE file {f} does not exist.".format(f=done)
        for pickle in splitted_pickles:
            if not nfs_exists(pickle):
                errMsg = "Pickle file {f} does not exist.".format(f=pickle)

        if len(errMsg) != 0:
            raise ValueError(errMsg)

        # root_dir/output/map_noFL/nfl.all.partial_uc.pickle
        out_pickle = icef.nfl_all_pickle_fn
        return (splitted_pickles, out_pickle)

    def run(self):
        """Run IcePartialMerge."""
        logging.debug("root_dir: {d}".format(d=self.root_dir))
        logging.debug("Total number of chunks N = {N}".format(N=self.N))

        splitted_pickles, out_pickle = self.validate_inputs()

        logging.info("Combining {N} nfl pickles.")
        combine_nfl_pickles(splitted_pickles, out_pickle)


# from pbcore.util.ToolRunner import PBToolRunner
# class IcePartialMergeRunner(PBToolRunner):
#
#     """IcePartialMerge runner."""
#
#     def __init__(self):
#         PBToolRunner.__init__(self, IcePartialMerge.desc)
#         self.parser = add_ice_partial_merge_arguments(self.parser)
#
#     def getVersion(self):
#         """Return version string."""
#         return get_version()
#
#     def run(self):
#         """Run"""
#         logging.info("Running {f} v{v}.".format(f=op.basename(__file__),
#                                                 v=get_version()))
#         cmd_str = ""
#         try:
#             args = self.args
#             obj = IcePartialMerge(root_dir=args.root_dir, N=args.N)
#             cmd_str = obj.cmd_str()
#             obj.run()
#         except:
#             logging.exception("Exiting '{cmd_str}' with return code 1.".
#                               format(cmd_str=cmd_str))
#             return 1
#         return 0
#
#
# def main():
#     """Main function."""
#     runner = IcePartialMerge()
#     return runner.start()
#
# if __name__ == "__main__":
#     sys.exit(main())
