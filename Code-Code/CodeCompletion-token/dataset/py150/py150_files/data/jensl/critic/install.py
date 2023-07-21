# -*- mode: python; encoding: utf-8 -*-
#
# Copyright 2012 Jens Lindström, Opera Software ASA
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy of
# the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.

import os
import sys
import stat

# To avoid accidentally creating files owned by root.
sys.dont_write_bytecode = True

# Python version check is done before imports below so
# that python 2.6/2.5 users can see the error message.
import pythonversion
pythonversion.check("""\
NOTE: This script must be run in the Python interpreter that will be
used to run Critic.
""")

if sys.flags.optimize > 0:
    print """
ERROR: Please run this script without -O or -OO options.
"""
    sys.exit(1)

import argparse
import installation
import subprocess
import traceback

parser = argparse.ArgumentParser(description="Critic installation script")

# Uses default values for everything that has a default value (and isn't
# overridden by other command-line arguments) and signals an error for anything
# that doesn't have a default value and isn't set by a command-line argument.
parser.add_argument("--headless", help=argparse.SUPPRESS, action="store_true")

parser.add_argument("--etc-dir", help="directory where the Critic system configuration is stored", action="store")
parser.add_argument("--install-dir", help="directory where the Critic source code is installed", action="store")
parser.add_argument("--data-dir", help="directory where Critic's persistent data files are stored", action="store")
parser.add_argument("--cache-dir", help="directory where Critic's temporary data files are stored", action="store")
parser.add_argument("--git-dir", help="directory where the main Git repositories are stored", action="store")
parser.add_argument("--log-dir", help="directory where Critic's log files are stored", action="store")
parser.add_argument("--run-dir", help="directory where Critic's runtime files are stored", action="store")

for module in installation.modules:
    if hasattr(module, "add_arguments"):
        module.add_arguments("install", parser)

arguments = parser.parse_args()

if os.getuid() != 0:
    print """
ERROR: This script must be run as root.
"""
    sys.exit(1)

if os.path.exists(os.path.join(installation.root_dir, ".installed")):
    print """
ERROR: Found an .installed file in the directory you're installing from.

This typically means that Critic is already installed on this system, and if so
then the upgrade.py script should be used to upgrade the installation rather than
re-running install.py.
"""
    sys.exit(1)

if arguments.headless:
    installation.input.headless = True

def abort():
    print
    print "ERROR: Installation aborted."
    print

    for module in reversed(installation.modules):
        try:
            if hasattr(module, "undo"):
                module.undo()
        except:
            print >>sys.stderr, "FAILED: %s.undo()" % module.__name__
            traceback.print_exc()

    sys.exit(1)

try:
    sha1 = "0" * 40

    # If Git is already installed, check for local modifications.  If Git isn't
    # installed (no 'git' executable in $PATH) then presumably we're not
    # installing from a repository clone, but from an exported tree, and in that
    # case we can't check for local modifications anyway.
    if installation.prereqs.git.check():
        git = installation.prereqs.git.path

        try:
            if installation.utils.run_git([git, "status", "--porcelain"],
                                          cwd=installation.root_dir).strip():
                print """
ERROR: This Git repository has local modifications.

Installing from a Git repository with local changes is not supported.
Please commit or stash the changes and then try again.
"""
                sys.exit(1)

            sha1 = installation.utils.run_git([git, "rev-parse", "HEAD"],
                                              cwd=installation.root_dir).strip()
        except subprocess.CalledProcessError:
            # Probably not a Git repository at all.
            pass

    data = { "sha1": sha1 }

    for module in installation.modules:
        try:
            if hasattr(module, "prepare") and not module.prepare("install", arguments, data):
                abort()
        except KeyboardInterrupt:
            abort()
        except SystemExit:
            raise
        except:
            print >>sys.stderr, "FAILED: %s.prepare()" % module.__name__
            traceback.print_exc()
            abort()

    print

    installed_file = os.path.join(installation.root_dir, ".installed")
    with open(installed_file, "w"):
        pass
    install_py_stat = os.stat(os.path.join(installation.root_dir, "install.py"))
    os.chown(installed_file, install_py_stat.st_uid, install_py_stat.st_gid)

    for module in installation.modules:
        try:
            if hasattr(module, "install") and not module.install(data):
                abort()
        except KeyboardInterrupt:
            abort()
        except SystemExit:
            raise
        except:
            print >>sys.stderr, "FAILED: %s.install()" % module.__name__
            traceback.print_exc()
            abort()

    for module in installation.modules:
        try:
            if hasattr(module, "finish"):
                module.finish("install", arguments, data)
        except:
            print >>sys.stderr, "WARNING: %s.finish() failed" % module.__name__
            traceback.print_exc()

    installation.utils.write_install_data(arguments, data)
    installation.utils.clean_root_pyc_files()

    print
    print "SUCCESS: Installation complete!"
    print
except SystemExit:
    raise
except:
    traceback.print_exc()
    abort()
