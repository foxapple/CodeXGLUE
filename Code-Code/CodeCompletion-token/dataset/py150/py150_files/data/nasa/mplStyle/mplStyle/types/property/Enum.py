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

""": Enum property module."""

__version__ = "$Revision: #1 $"

#===========================================================================
from ..StyleProperty import StyleProperty

from .. import convert as cvt
#===========================================================================

__all__ = [ 'Enum' ]

#===========================================================================
class Enum( StyleProperty ):
   """: A Enum style property.
   """

   #-----------------------------------------------------------------------
   def __init__( self, enumDict, caseInsens=None, default=None, doc=None ):
      """: Create a new Enum object.

      = INPUT VARIABLES
      - enumDict    The conversion dictionary.
      - caseInsens  If True, then the string is case insensitive.  If
                    None and the first enum is a string, this will be set
                    to True.
      - default     The default value that instances will be initialized with.
      - doc         The docstring for this property.
      """
      if doc is None:
         doc = "\nAn enumeration.  Can be one of the following:\n\n"
         keys = enumDict.keys()
         keys.sort()
         for k in keys:
            doc += "   + '%s'\n" % ( enumDict[k], )
         doc += "\n"

      self.enumDict = enumDict

      if caseInsens is None:
         keys = self.enumDict.keys()
         if keys and isinstance( keys[0], str ):
            caseInsens = True

      validator = cvt.Converter( cvt.toEnum, enumDict,
                                 allowNone=True, caseInsens = caseInsens )
      StyleProperty.__init__( self, default, validator, doc )

   #-----------------------------------------------------------------------

