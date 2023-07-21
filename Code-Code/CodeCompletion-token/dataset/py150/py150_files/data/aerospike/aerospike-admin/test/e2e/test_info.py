# Copyright 2013-2016 Aerospike, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import test_util
import unittest2 as unittest
import lib.util as util
import lib.controller as controller


class TestInfo(unittest.TestCase):
    
    rc = None
    output_list = list()
    service_info = ''
    network_info = ''
    namespace_info = ''
    sindex_info = ''
    xdr_info = ''
    
    @classmethod
    def setUpClass(cls):
        TestInfo.rc = controller.RootController()
        actual_out = util.capture_stdout(TestInfo.rc.execute, ['info'])
        TestInfo.output_list = test_util.get_separate_output(actual_out, 'Information')
        # TestInfo.output_list.append(util.capture_stdout(TestInfo.rc.execute, ['info', 'sindex']))            
        for item in TestInfo.output_list:
            if "~~Network Information~~" in item:
                TestInfo.network_info = item           
            elif "~~Namespace Information~~" in item:
                TestInfo.namespace_info = item               
            elif "~~Secondary Index Information~~" in item:
                TestInfo.sindex_info = item              
            elif "~~XDR Information~~" in item:
                TestInfo.xdr_info = item
        
    @classmethod    
    def tearDownClass(self):
        self.rc = None    

    def test_network(self):
        """
        This test will assert <b> info Network </b> output for heading, headerline1, headerline2
        and no of row displayed in output
        ToDo: test for values as well
        """
        exp_heading = "~~Network Information~~"
        exp_header = [   'Node',
                         'Node Id',
                         'Ip',
                         'Build',
                         'Cluster Size',
                         'Cluster Key',
                         'Cluster Integrity',
                         'Principal',
                         'Client Conns',
                         'Uptime']
        exp_no_of_rows = len(TestInfo.rc.cluster.nodes)
        
        actual_heading, actual_header, actual_no_of_rows = test_util.parse_output(TestInfo.network_info, horizontal = True)        
        
        self.assertTrue(exp_heading in actual_heading)
        self.assertEqual(exp_header, actual_header)
        self.assertEqual(exp_no_of_rows, int(actual_no_of_rows.strip()))

    @unittest.skip("Skipping by default, to make it work please enable in setupClass also")
    def test_sindex(self):
        """
        This test will assert <b> info sindex </b> output for heading, headerline1, headerline2
        and no of row displayed in output
        ToDo: test for values as well
        """
        exp_heading = '~~Secondary Index Information~~'
        exp_header = ['Node', 
                      'Index Name', 
                      'Namespace', 
                      'Set', 
                      'Bins', 
                      'Num Bins', 
                      'Bin Type', 
                      'State', 
                      'Sync State']
        exp_no_of_rows = len(TestInfo.rc.cluster.nodes)
        
        actual_heading, actual_header, actual_no_of_rows = test_util.parse_output(TestInfo.sindex_info, horizontal = True)        
        
        self.assertTrue(exp_heading in actual_heading)
        self.assertEqual(exp_header, actual_header)

    def test_namespace(self):
        """
        This test will assert <b> info Namespace </b> output for heading, headerline1, headerline2
        and no of row displayed in output
        ToDo: test for values as well
        """
        exp_heading = "~~Namespace Information~~"
        exp_header = [   'Node',
                         'Namespace',
                         'Evictions',
                         'Master Objects',
                         'Replica Objects',
                         'Repl Factor',
                         'Stop Writes',
                         'HWM Disk%',
                         'Mem Used',
                         'Mem Used%',
                         'HWM Mem%',
                         'Stop Writes%']
        exp_no_of_rows = len(TestInfo.rc.cluster.nodes)
        
        actual_heading, actual_header, actual_no_of_rows = test_util.parse_output(TestInfo.namespace_info, horizontal = True)        
        self.assertTrue(set(exp_header).issubset(set(actual_header)))
        self.assertTrue(exp_heading in actual_heading)

    @unittest.skip("Will enable only when xdr is configuired")
    def test_xdr(self):
        """
        This test will assert <b> info Namespace </b> output for heading, headerline1, headerline2
        and no of row displayed in output
        ToDo: test for values as well
        """
        exp_heading = "~~XDR Information~~"
        exp_header = ['Node', 
                      'Build', 
                      'Data Shipped', 
                      'Free Dlog%', 
                      'Lag (sec)', 
                      'Req Outstanding', 
                      'Req Relog', 
                      'Req Shipped', 
                      'Cur Throughput', 
                      'Avg Latency', 
                      'Xdr Uptime']
        exp_no_of_rows = len(TestInfo.rc.cluster.nodes)
        
        actual_heading, actual_header, actual_no_of_rows = test_util.parse_output(TestInfo.xdr_info, horizontal = True)        
        self.assertEqual(exp_header, actual_header)
        self.assertTrue(exp_heading in actual_heading)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
