#!/usr/bin/env python
"""Given input.fofn, for each movie.bas|bax.h5 file in the fofn,
call pls2fasta to generate a movie.bax|bas.h5.fasta file in a
specified directory, and then trim both ends of each read in fasta
files. Finally, add all these fasta files to fasta_fofn
(e.g., input.fasta.fofn).
"""

import logging
import sys
import os.path as op
from pbtools.pbtranscript.__init__ import get_version
from pbtools.pbtranscript.ice.IceUtils import convert_fofn_to_fasta


def set_parser(parser):
    """Get arguments."""
    parser.add_argument("input_fofn",
                        help="Input bax.h5 fofn, e.g., input.fofn")
    parser.add_argument("fasta_fofn",
                        help="Output fasta fofn, e.g., input.fasta.fofn")
    parser.add_argument("fasta_out_dir",
                        help="Where to save generated fasta files")


from pbcore.util.ToolRunner import PBToolRunner


class MakeFastaFofnRunner(PBToolRunner):

    """ice_make_input_fasta_fofn runner."""

    def __init__(self):
        desc = "Converting bas/bax.h5 files within a fofn to fasta " + \
               "files and create a fasta fofn."
        PBToolRunner.__init__(self, desc)
        set_parser(self.parser)

    def getVersion(self):
        """Return version string."""
        return get_version()

    def run(self):
        """Run"""
        logging.info("Running {f} v{v}.".format(f=op.basename(__file__),
                                                v=get_version()))
        args = self.args
        try:
            convert_fofn_to_fasta(fofn_filename=args.input_fofn,
                                  out_filename=args.fasta_fofn,
                                  fasta_out_dir=args.fasta_out_dir,
                                  force_overwrite=False)
        except:
            logging.exception("Failed to convert fofn {f} to fasta.".
                              format(fofn=args.input_fofn))
            return 1
        return 0


def main():
    """Main function."""
    runner = MakeFastaFofnRunner()
    return runner.start()

if __name__ == "__main__":
    sys.exit(main())
