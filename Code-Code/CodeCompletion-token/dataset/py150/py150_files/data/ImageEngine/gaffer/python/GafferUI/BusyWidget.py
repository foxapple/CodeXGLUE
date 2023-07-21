##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import math
import time

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class BusyWidget( GafferUI.Widget ) :

	def __init__( self, size = 50, parenting = None ) :

		GafferUI.Widget.__init__( self, _BusyWidget( None, size ), parenting = parenting )

# qt implementation class
class _BusyWidget( QtGui.QWidget ) :

	def __init__( self, parent = None , size = 50 ) :

		QtGui.QWidget.__init__( self, parent )

		self.__size = size
		self.setMinimumSize( size, size )
		self.__timer = None

	def showEvent( self, event ) :

		QtGui.QWidget.showEvent( self, event )

		if self.__timer is None :
			self.__timer = self.startTimer( 1000 / 25 )

	def hideEvent( self, event ) :

		QtGui.QWidget.hideEvent( self, event )

		if self.__timer is not None :
			self.killTimer( self.__timer )
			self.__timer = None

	def timerEvent( self, event ) :

		self.update()

	def paintEvent( self, event ) :

		painter = QtGui.QPainter( self )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		width, height = float( self.width() ), float( self.height() )
		centreX, centreY = width / 2, height / 2
		radius = self.__size / 2.0
		numCircles = 10
		circleRadius = radius / 5
		penWidth = circleRadius / 10

		for i in range( 0, numCircles ) :

			theta = i * 360.0 / numCircles + time.time() * 10
			circleCentreX = centreX - (radius - circleRadius - penWidth) * math.cos( math.radians( theta ) )
			circleCentreY = centreY + (radius - circleRadius - penWidth) * math.sin( math.radians( theta ) )

			alpha =  1 - ( ( math.fmod( theta + time.time() * 270, 360 ) ) / 360 )

			## \todo Colours (and maybe even drawing) should come from style
			brush = QtGui.QBrush( QtGui.QColor( 119, 156, 189, alpha * 255 ) )
			painter.setBrush( brush )

			pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, alpha * 255 ) )
			pen.setWidth( penWidth )
			painter.setPen( pen )

			painter.drawEllipse( QtCore.QPointF( circleCentreX, circleCentreY ), circleRadius, circleRadius )
