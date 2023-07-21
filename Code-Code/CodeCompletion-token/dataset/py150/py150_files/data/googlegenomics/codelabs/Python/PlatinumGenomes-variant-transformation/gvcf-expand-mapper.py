#!/usr/bin/env python

# Copyright 2014 Google Inc. All Rights Reserved.
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

"""A mapper for expansion of gVCF and CGI data.

To test locally, set both BIG_QUERY_SOURCE and BIG_QUERY_SINK to False and run:
  cat ./data/platinum-genomes-brca1.json | ./gvcf-expand-mapper.py | sort \
  | ./gvcf-expand-reducer.py > out.json
"""

import json
import sys

from gvcf_expander import GvcfExpander

# Whether the source data from this job is coming from the BigQuery connector
# for Hadoop Streaming
BIG_QUERY_SOURCE = True


def main():
  """Entry point to the script."""

  # Basic parsing of command line arguments to allow a filename
  # to be passed when running this code in the debugger.
  file_handle = sys.stdin
  if 2 <= len(sys.argv):
    file_handle = open(sys.argv[1], "r")

  expander = GvcfExpander(bin_size=1000,
                          filter_ref_matches=False,
                          emit_ref_blocks=False)

  line = file_handle.readline()
  while line:
    line = line.strip()
    if not line:
      line = file_handle.readline()
      continue

    if BIG_QUERY_SOURCE:
      (key, value) = line.split("\t")
      fields = json.loads(value)
    else:
      fields = json.loads(line)

    pairs = expander.map(fields=fields)
    for pair in pairs:
      emit(pair.k, pair.v)

    line = file_handle.readline()


def emit(key, fields):
  """Emits a key/value pair to stdout.

  Args:
    key: (string)
    fields: (dictionary)

  Returns: n/a

  Side Effects:
    a VCF line is written to stdout
  """
  print "%s\t%s" % (key, json.dumps(fields))


if __name__ == "__main__":
  main()
