#===========================================================================
#
# Copyright (c) 2014, California Institute of Technology.
# U.S. Government Sponsorship under NASA Contract NAS7-03001 is
# acknowledged.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#===========================================================================

"The ToExactListOf unit test."

__version__ = "$Revision: #1 $"

#===========================================================================
# Reqmtypes.ed imports.  Do not modify these.
import unittest

#===========================================================================
# Place all imports after here.
#
import os
import mplStyle.types.convert as cvt
#
# Place all imports before here.
#===========================================================================

#===========================================================================
class TesttoExactListOf( unittest.TestCase ):
   """ToExactListOf module."""

   #-----------------------------------------------------------------------
   def setUp( self ):
      """This method is called before any tests are run."""
      
      # You may place initialization code here.


   #-----------------------------------------------------------------------
   def tearDown( self ):
      """This method is called after all tests are run."""
      pass
   #=======================================================================
   # Add tests methods below.
   # Any method whose name begins with 'test' will be run by the framework.
   #=======================================================================
   def testToExactListOf( self ):
      """Test the ToExactListOf converter."""

      # Test the case with only one element.
      converter = cvt.toExactListOf
      cvtList = [ cvt.Converter( cvt.toType, float, allowNone=False ) ]

      d1 = "10"
      right = [ 10 ]

      result = converter( [ d1 ], cvtList )
      self.assertEqual( right, result,
               "Incorrect conversion of list with one element." )

      self.assertRaises( Exception, converter, d1, cvtList, name='value',
                   msg="Use non-list argument should be an error." )
      self.assertRaises( Exception, converter, [ d1, d1 ], cvtList,
                         name='value',
                   msg="Use list with wrong size should be an error." )
      self.assertRaises( Exception, converter, [ "foo bar" ], cvtList,
                         name='value',
                   msg="Use list with wrong type should be an error." )
      self.assertRaises( Exception, converter, None, cvtList, name='value',
                   msg="Use None with AllowNone=False should be an error." )

      # Test the case with multiple elements.
      cvtList = [ cvt.Converter( cvt.toType, float ),
                  cvt.Converter( cvt.toType, str ) ]

      s1 = "test"
      f1 = "123"
      right = [ 123.0, "test" ]

      result = converter( [ f1, s1 ], cvtList )
      self.assertEqual( right, result,
                        "Incorrect conversion of list with multiple elements." )

      result = converter( ( f1, s1 ), cvtList )
      self.assertEqual( right, result, "Incorrect conversion of tuple." )

      self.assertRaises( Exception, converter, s1, cvtList,
                   msg="Use non-list argument should be an error." )
      self.assertRaises( Exception, converter, [ s1 ], cvtList,
                   msg="Use list with wrong size should be an error." )
      self.assertRaises( Exception, converter, [ f1, s1 ], cvtList,
                   msg="Use list with wrong order should be an error." )
      self.assertRaises( Exception, converter, None, cvtList,
                   msg="Use None with AllowNone=False should be an error." )
 
   #-----------------------------------------------------------------------
   def testAllowNone( self ):
      """Test allow none."""
      
      converter = cvt.toExactListOf
      cvtList = [ cvt.Converter( cvt.toType, float ) ]

      result = converter( None, cvtList, allowNone=True )
      self.assertEqual( None, result, "Incorrect conversion of none." )

      s1 = "123"
      right = [ 123 ]

      result = converter( [ s1 ], cvtList, allowNone=True )
      self.assertEqual( right, result, "Incorrect conversion with allow none." )

#===========================================================================
