"""Start the arcyd instance for the current directory, if not already going."""
# =============================================================================
# CONTENTS
# -----------------------------------------------------------------------------
# abdcmd_start
#
# Public Functions:
#   getFromfilePrefixChars
#   setupParser
#   process
#
# -----------------------------------------------------------------------------
# (this contents block is generated, edits will be lost)
# =============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import abdi_startstop


def getFromfilePrefixChars():
    return None


def setupParser(parser):
    parser.add_argument(
        '--foreground',
        '-f',
        action='store_true',
        help="supply this argument to run arcyd interactively in the "
             "foreground")
    parser.add_argument(
        '--no-loop',
        action='store_true',
        help="supply this argument to only process each repo once then exit")


def process(args):
    logging.getLogger().setLevel(logging.DEBUG)
    abdi_startstop.start_arcyd(daemonize=not args.foreground,
                               loop=not args.no_loop)

# -----------------------------------------------------------------------------
# Copyright (C) 2014-2015 Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------ END-OF-FILE ----------------------------------
