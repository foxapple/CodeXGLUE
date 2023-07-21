#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, Jean-Rémy Bancel <jean-remy.bancel@telecom-paristech.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Chromagon Project nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Jean-Rémy Bancel BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Frontend script using Chrome Cache parsing library
"""

import argparse
import textwrap

import chromagnon.cacheParse

def main():
    parser = argparse.ArgumentParser(
             formatter_class=argparse.RawDescriptionHelpFormatter,
             description=textwrap.dedent('''
\033[32mChromagnon Chrome Cache Parser\033[0m

\033[4mTwo input methods\033[0m
   1) A list of urls (usefull if you want to analyse only know urls).
      The entry corresponding to the url is found in the hash table,
      so it is fast.
   2) Parse the whole cash by not specifying urls. Usefull to get
      an exhaustive idea of what is in the cache. Can be slow if the
      cache has numerous entries.

\033[4mThree output methods\033[0m
   1) Terminal output. Displays main details of each cache entry.
      Stderr is used for error messages.
   2) Export to files. The entries are exported to the given directory
      (specified with \033[1m-o\033[0m option). It is browsable with a web browser.
   3) Output a csv file to terminal compliant with log2timeline.
      \033[1m-l2t\033[0m flag.
             '''),
             epilog=textwrap.dedent('''
\033[4mExamples\033[0m
    - Export the whole cache to browse it

     > python chromagnonCache.py ~/.cache/chromium/Default/Cache/ -o /tmp/export

    - Export the whole cache and read it with log2timeline

     > python chromagnonCache.py ~/.cache/chromium/Default/Cache/ -l2t > l2t.csv
     > log2timeline -f l2t_csv l2t.csv

    - Displaying informations about a url
     > python chromagnonCache.py ~/.cache/chromium/Default/Cache/ -u "http://test.com"
                     '''))
    parser.add_argument("Cache Directory", action='store',
                        help="Chrome Cache Directory")
    parser.add_argument("-o", "-output", action='store',
                        default=None,
                        help="Export cached data to that directory \
                        (created if it doesn't exist)")
    parser.add_argument("-l2t", "-log2timeline", action='store_true',
                        default=False,
                        help="Use csv log2timeline format for output")
    parser.add_argument("-u", "-urls", action='store', nargs="+",
                        help="Use given urls as input")
    args = parser.parse_args()

    # Getting data
    cache = chromagnon.cacheParse.parse(
            args.__getattribute__("Cache Directory"), args.u)

    # Export or display
    if args.o == None:
        if args.l2t:
            chromagnon.cacheParse.exportTol2t(cache)
        else:
            for entry in cache:
                print entry
                print "-"*80
    else:
        chromagnon.cacheParse.exportToHTML(cache, args.o)

if __name__ == "__main__":
    main()
