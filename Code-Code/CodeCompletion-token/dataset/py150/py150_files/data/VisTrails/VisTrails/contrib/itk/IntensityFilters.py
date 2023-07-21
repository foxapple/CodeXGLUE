#############################################################################
##
## Copyright (C) 2006-2007 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at contact@vistrails.org.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
import itk
import core.modules
from core.modules.vistrails_module import Module, ModuleError

from ITK import *
from Image import Image

class RescaleIntensityImageFilter(Module):
    my_namespace = "Filter|Intensity"
    def compute(self):
        im = self.get_input("Input Image")

        #check for input PixelType
        if self.has_input("Input PixelType"):
            inPixelType = self.get_input("Input PixelType")
        else:
            inPixelType = im.getPixelType()

        #check for output PixelType
        if self.has_input("Output PixelType"):
            outPixelType = self.get_input("Output PixelType")
        else:
            outPixelType = inPixelType

        #check for dimension
        if self.has_input("Dimension"):
            dim = self.get_input("Dimension")
        else:
            dim = im.getDim()

        #set up filter
        inImgType = itk.Image[inPixelType._type, dim]
        outImgType = itk.Image[outPixelType._type, dim]

        minimum = self.get_input("Minimum")
        maximum = self.get_input("Maximum")

        self.filter_ = itk.RescaleIntensityImageFilter[inImgType, outImgType].New(im.getImg())
        self.filter_.SetOutputMaximum(maximum)
        self.filter_.SetOutputMinimum(minimum)

        self.filter_.Update()

        #setup output image
        outIm = Image()
        outIm.setImg(self.filter_.GetOutput())
        outIm.setPixelType(outPixelType)
        outIm.setDim(dim)

        #set results
        self.set_output("Output Image", outIm)
        self.set_output("Filter", self)
        self.set_output("Output PixelType", outPixelType)

    @classmethod
    def register(cls, reg, basic):
        reg.add_module(cls, name="Rescale Intensity Image Filter", namespace=cls.my_namespace)

        reg.add_input_port(cls, "Input Image", (Image, 'Input Image'))
        reg.add_input_port(cls, "Input PixelType", (PixelType, 'Input PixelType'),True)
        reg.add_input_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)
        reg.add_input_port(cls, "Dimension", (basic.Integer, 'Dimension'),True)
        reg.add_input_port(cls, "Minimum", (basic.Integer, 'Minimum'))
        reg.add_input_port(cls, "Maximum", (basic.Integer, 'Maximum'))

        reg.add_output_port(cls, "Output Image", (Image, 'Output Image'))
        reg.add_output_port(cls, "Filter", (Filter, 'Filter'), True)
        reg.add_output_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)

class SigmoidImageFilter(Module):
    my_namespace = "Filter|Intensity"
    def compute(self):
        im = self.get_input("Input Image")

        #check for input PixelType
        if self.has_input("Input PixelType"):
            inPixelType = self.get_input("Input PixelType")
        else:
            inPixelType = im.getPixelType()

        #check for output PixelType
        if self.has_input("Output PixelType"):
            outPixelType = self.get_input("Output PixelType")
        else:
            outPixelType = inPixelType

        #check for dimension
        if self.has_input("Dimension"):
            dim = self.get_input("Dimension")
        else:
            dim = im.getDim()

        #set up filter
        inImgType = itk.Image[inPixelType._type, dim]
        outImgType = itk.Image[outPixelType._type, dim]

        #default values are those that are recommended
        if self.has_input("Minimum"):
            min = self.get_input("Minimum")
        else:
            min = 10

        if self.has_input("Maximum"):
            max = self.get_input("Maximum")
        else:
            max = 240

        if self.has_input("Alpha"):
            alpha = self.get_input("Alpha")
        else:
            alpha = 10

        if self.has_input("Beta"):
            beta = self.get_input("Beta")
        else:
            beta = 170

        self.filter_ = itk.SigmoidImageFilter[inImgType,outImgType].New(im.getImg())
        self.filter_.SetOutputMinimum(min)
        self.filter_.SetOutputMaximum(max)
        self.filter_.SetAlpha(alpha)
        self.filter_.SetBeta(beta)
        self.filter_.Update()

        #setup output image
        outIm = Image()
        outIm.setImg(self.filter_.GetOutput())
        outIm.setPixelType(outPixelType)
        outIm.setDim(dim)
        
        self.set_output("Output Image", outIm)
        self.set_output("Filter", self)
        self.set_output("Output PixelType", outPixelType)

    @classmethod
    def register(cls, reg, basic):
        reg.add_module(cls, name="Sigmoid Image Filter", namespace=cls.my_namespace)

        reg.add_input_port(cls, "Input Image", (Image, 'Input Image'))
        reg.add_input_port(cls, "Input PixelType", (PixelType, 'Input PixelType'),True)
        reg.add_input_port(cls, "Output PixelType", (PixelType, 'Output PixelType'), True)
        reg.add_input_port(cls, "Dimension", (basic.Integer, 'Dimension'),True)
        reg.add_input_port(cls, "Minimum", (basic.Integer, 'Minimum'), True)
        reg.add_input_port(cls, "Maximum", (basic.Integer, 'Maximum'), True)
        reg.add_input_port(cls, "Alpha", (basic.Float, 'Alpha'), True)
        reg.add_input_port(cls, "Beta", (basic.Float, 'Beta'), True)

        reg.add_output_port(cls, "Output Image", (Image, 'Output Image'))
        reg.add_output_port(cls, "Filter", (Filter, 'Output Filter'),True)
        reg.add_output_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)

class ThresholdImageFilter(Module):
    my_namespace = "Filter|Intensity"
    def compute(self):
        im = self.get_input("Input Image")

        #check for input PixelType
        if self.has_input("Input PixelType"):
            inPixelType = self.get_input("Input PixelType")
        else:
            inPixelType = im.getPixelType()

        #check for dimension
        if self.has_input("Dimension"):
            dim = self.get_input("Dimension")
        else:
            dim = im.getDim()

        #setup filter
        inImgType = itk.Image[inPixelType._type, dim]
        up = self.get_input("Upper Value")
        lo = self.get_input("Lower Value")

        self.filter_ = itk.ThresholdImageFilter[inImgType].New(im.getImg())

        self.filter_.SetUpper(up)
        self.filter_.SetLower(lo)
#       self.filter_.ThresholdAbove(up)
        self.filter_.Update()

        #setup output image
        outIm = Image()
        outIm.setImg(self.filter_.GetOutput())
        outIm.setPixelType(inPixelType)
        outIm.setDim(dim)

        self.set_output("Output Image", outIm)

    @classmethod
    def register(cls, reg, basic):
        reg.add_module(cls, name="Threshold Image Filter", namespace=cls.my_namespace)

        reg.add_input_port(cls, "Input Image", (Image, 'Input Image'))
        reg.add_input_port(cls, "Dimension", (basic.Integer, 'Dimension'),True)
        reg.add_input_port(cls, "Input PixelType", (PixelType, 'Input PixelType'),True)
        reg.add_input_port(cls, "Upper Value", (basic.Integer, 'Upper Value'))
        reg.add_input_port(cls, "Lower Value", (basic.Integer, 'Lower Value'))

        reg.add_output_port(cls, "Output Image", (Image, 'Output Image'))

class ShiftScaleImageFilter(Module):
    my_namespace = "Filter|Intensity"

    def compute(self):
        im = self.get_input("Input Image")

        #check for input PixelType
        if self.has_input("Input PixelType"):
            inPixelType = self.get_input("Input PixelType")
        else:
            inPixelType = im.getPixelType()

        #check for output PixelType
        if self.has_input("Output PixelType"):
            outPixelType = self.get_input("Output PixelType")
        else:
            outPixelType = inPixelType

        #check for dimension
        if self.has_input("Dimension"):
            dim = self.get_input("Dimension")
        else:
            dim = im.getDim()

        #set up filter
        inImgType = itk.Image[inPixelType._type, dim]
        outImgType = itk.Image[outPixelType._type, dim]

        shift_value = self.get_input("Shift Value")

        scale_value = self.get_input("Scale Value")

        self.filter_ = itk.ShiftScaleImageFilter[inImgType, outImgType].New(im.getImg())
        self.filter_.SetShift(shift_value)
        self.filter_.SetScale(scale_value)
        self.filter_.Update()

        #setup output image
        outIm = Image()
        outIm.setImg(self.filter_.GetOutput())
        outIm.setPixelType(outPixelType)
        outIm.setDim(dim)

        #set results
        self.set_output("Output Image", outIm)
        self.set_output("Filter", self)
        self.set_output("Output PixelType", outPixelType)


    @classmethod
    def register(cls, reg, basic):
        reg.add_module(cls, name="Shift Scale Image Filter", namespace=cls.my_namespace)

        reg.add_input_port(cls, "Input Image", (Image, 'Input Image'))
        reg.add_input_port(cls, "Input PixelType", (PixelType, 'Input PixelType'),True)
        reg.add_input_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)
        reg.add_input_port(cls, "Dimension", (basic.Integer, 'Dimension'),True)

        reg.add_input_port(cls, "Shift Value", (basic.Float, 'Shift Value'))
        reg.add_input_port(cls, "Scale Value", (basic.Integer, 'Scale Value'))

        reg.add_output_port(cls, "Output Image", (Image, 'Output Image'))
        reg.add_output_port(cls, "Filter", (Filter, 'Filter'), True)
        reg.add_output_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)

class NormalizeImageFilter(Module):
    my_namespace = 'Filter|Intensity'

    def compute(self):
        im = self.get_input("Input Image")

        #check for input PixelType
        if self.has_input("Input PixelType"):
            inPixelType = self.get_input("Input PixelType")
        else:
            inPixelType = im.getPixelType()

        #check for output PixelType
        if self.has_input("Output PixelType"):
            outPixelType = self.get_input("Output PixelType")
        else:
            outPixelType = inPixelType

        #check for dimension
        if self.has_input("Dimension"):
            dim = self.get_input("Dimension")
        else:
            dim = im.getDim()

        #set up filter
        inImgType = itk.Image[inPixelType._type, dim]
        outImgType = itk.Image[outPixelType._type, dim]

        self.filter_ = itk.NormalizeImageFilter[inImgType, outImgType].New(im.getImg())
        self.filter_.Update()

        #setup output image
        outIm = Image()
        outIm.setImg(self.filter_.GetOutput())
        outIm.setPixelType(outPixelType)
        outIm.setDim(dim)

        #set results
        self.set_output("Output Image", outIm)
        self.set_output("Filter", self)
        self.set_output("Output PixelType", outPixelType)


    @classmethod
    def register(cls, reg, basic):
        reg.add_module(cls, name="Normalize Image Filter", namespace=cls.my_namespace)

        reg.add_input_port(cls, "Input Image", (Image, 'Input Image'))
        reg.add_input_port(cls, "Input PixelType", (PixelType, 'Input PixelType'),True)
        reg.add_input_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)
        reg.add_input_port(cls, "Dimension", (basic.Integer, 'Dimension'),True)


        reg.add_output_port(cls, "Output Image", (Image, 'Output Image'))
        reg.add_output_port(cls, "Filter", (Filter, 'Filter'), True)
        reg.add_output_port(cls, "Output PixelType", (PixelType, 'Output PixelType'),True)

