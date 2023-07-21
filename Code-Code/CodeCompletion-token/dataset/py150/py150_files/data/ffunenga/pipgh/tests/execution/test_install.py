from __future__ import print_function
import unittest
import subprocess

import pipgh


class TestInstall(unittest.TestCase):

    def test_execution_fullname(self):
        argv = ['install', 'nvie/times']
        pipgh.install(False, argv, dry_run=False, output=False)
        rst = subprocess.check_output(['pip', 'freeze'], stderr=subprocess.PIPE)
        self.assertTrue(any(l.startswith(u'times'.encode('utf-8'))
                            for l in rst.split()))

    def test_execution_fullname_ref(self):
        argv = ['install', 'crsmithdev/arrow', '0.5.3']
        pipgh.install(False, argv, dry_run=False, output=False)
        rst = subprocess.check_output(['pip', 'freeze'], stderr=subprocess.PIPE)
        self.assertTrue(any(l.startswith(u'arrow'.encode('utf-8'))
                            for l in rst.split()))

    def test_execution_requirements(self):
        argv = ['install', '-r', 'tests/execution/requirements.txt']
        pipgh.install(False, argv, dry_run=False, output=False)
        rst = subprocess.check_output(['pip', 'freeze'], stderr=subprocess.PIPE)
        #
        self.assertTrue(any(l.startswith(u'docopt'.encode('utf-8'))
                            for l in rst.split()))

