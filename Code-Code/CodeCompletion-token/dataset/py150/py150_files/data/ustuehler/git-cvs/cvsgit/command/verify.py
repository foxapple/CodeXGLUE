"""Command to compare a Git tree against CVS."""

import os
import re
import subprocess
from subprocess import PIPE
import sys

from cvsgit.cvs import split_cvs_source
from cvsgit.git import GitCommandError
from cvsgit.i18n import _
from cvsgit.main import Command, Conduit
from cvsgit.utils import Tempdir, stripnl

class Verify(Command):
    __doc__ = _(
    """Verify the Git work tree against CVS.

    Usage: %prog

    Compares the work tree against a clean checkout from CVS with the
    same timestamp as the HEAD commit.
    """)

    def initialize_options(self):
        self.commit = 'HEAD'
        self.add_option('--history', action='store_true', help=\
            _("Walk backwards through the entire history."))
        self.add_option('--forward', action='store_true', help=\
            _("Modifies the --history option to walk forward."))
        self.add_option('--skip', action='store_true', help=\
            _("Skip the first verification step and move HEAD "
              "backward instead, the opposite direction with "
              "--forward)."))
        self.add_option('--quiet', action='store_true', help=\
            _("Only report error and warning messages."))

    def finalize_options(self):
        if len(self.args) > 0:
            self.usage_error(_('too many arguments'))

    def run(self):
        conduit = Conduit()
        self.cvsroot, self.module = split_cvs_source(conduit.source)
        self.git = git = conduit.git
        with Tempdir() as tempdir:
            self.tempdir = tempdir

            while True:
                if self.options.skip:
                    self.options.skip = False
                else:
                    returncode = self._run()
                    if returncode != 0:
                        return returncode
                    elif not self.options.history:
                        return 0

                if self.options.forward:
                    wc_head = self.git.rev_parse('HEAD')
                    cvs_head = self.git.rev_parse(conduit.branch)
                    if wc_head == cvs_head:
                        return 0
                    subprocess.check_call(['/bin/sh', '-c',
                       'git checkout `git rev-list %s..%s|tail -1`' % \
                       (wc_head, cvs_head)])
                else:
                    try:
                        self.git.checkout('-q', 'HEAD~1')
                    except GitCommandError:
                        return 0

    def _run(self):
        returncode = 0
        date = self.commit_date(self.commit)
        head = self.git.rev_parse('--short', 'HEAD')
        command = ['cvs', '-Q', '-d', self.cvsroot, 'checkout',
                   '-P', '-D', date, '-d', self.tempdir, self.module]
        if not self.options.quiet:
            print "(%s) '%s'" % (head, "' '".join(command))
        # At least with OpenBSD's version of GNU CVS it is not
        # possible to run "cvs checkout" from a directory that's
        # inside the CVS repository.  This should avoid the
        # issue... *grrrr* The error is: cvs [checkout aborted]:
        # Cannot check out files into the repository itself
        try:
            owd = os.getcwd()
            os.chdir('/')
            subprocess.check_call(command)
        finally:
            os.chdir(owd)
        command = ['diff', '-r', self.tempdir, self.git.git_work_tree]
        pipe = subprocess.Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, dummy = pipe.communicate()
        for line in stripnl(stdout).split('\n'):
            if re.match('^Only in .+: \.git$', line):
                continue
            if re.match('^Only in .+: CVS$', line):
                continue
            if not self.options.quiet:
                sys.stdout.write(line + '\n')
            returncode = 1
        return returncode

    def commit_date(self, commit):
        """Get the commit date as a string in UTC timezone.
        """
        command = ['git', 'log', '-1', commit]
        pipe = self.git._popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = pipe.communicate()
        if pipe.returncode != 0:
            self.fatal(_("can't get commit date of %s" % commit))
        match = re.search('Date: +[^ ]+ (.*) \+0000', stdout)
        if match:
            return '%s UTC' % match.group(1)
        else:
            self.fatal(_("couldn't match Date: in output of '%s'") % \
                           ' '.join(command))
