import unittest
from mash import BaseCommand

class testBaseCommand(unittest.TestCase):
    def testArgs(self):
        # Mock args
        args = ['config:add', 'a=1', '--server', 'dev']
        command = BaseCommand(args)
        
