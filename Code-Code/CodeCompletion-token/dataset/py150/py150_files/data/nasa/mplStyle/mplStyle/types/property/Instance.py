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

""": Instance property module."""

__version__ = "$Revision: #1 $"

#===========================================================================
from ..StyleProperty import StyleProperty

import inspect

from .. import convert as cvt
#===========================================================================

__all__ = [ 'Instance' ]

#===========================================================================
class Instance( StyleProperty ):
   """: A Instance style property.
   """

   #-----------------------------------------------------------------------
   def __init__( self, cls, default = None, doc = "" ):
      """: Create a new Instance object.

      = INPUT VARIABLES
      - cls         The class type this is validated to.
      - default     The default value that instances will be initialized with.
      - doc         The docstring for this property.
      """
      #FUTURE: This should be handled better
      modulepath = inspect.getmodule( cls ).__name__
      modulepath = modulepath.replace( '.', '_' )

      doc += "\nThe value must be an instance of class " \
             "':ref:`%s <%s_%s>`'." % (cls.__name__, modulepath, cls.__name__)

      validator = cvt.Converter( cvt.toInstance, cls, allowNone=True )
      StyleProperty.__init__( self, default, validator, doc )

   #-----------------------------------------------------------------------

