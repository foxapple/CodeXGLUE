# ----------------------------------------------------------------------------
# Copyright 2015 Grammarly, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------
from quagga.matrix import Matrix
from quagga.context import Context
from quagga.connector import Connector


class MeanPoolingBlock(object):
    """
    MeanPoolingBlock pools matrix along the specified axis. Can handle matrix with
    varying number of columns. Number of rows is fixed.

    Parameters
    ----------
    matrix : Matrix (GpuMatrix or CpuMatrix)
    axis : int
    device_id : int
        Defines the device's id on which the computation will take place

    Returns
    -------
    """

    def __init__(self, matrix, axis=1, device_id=None):
        self.context = Context(device_id)
        self._ctype = matrix.c_dtype
        self._zero = self._ctype(0.0)
        if axis == 0:
            self._ones = Matrix.empty(1, matrix.nrows, matrix.dtype, device_id)
            self.output = Matrix.empty(1, matrix.ncols, matrix.dtype, device_id)
            self.alpha = self._ctype(1.0 / matrix.nrows)
        elif axis == 1:
            self._ones = Matrix.empty(matrix.ncols, 1, matrix.dtype, device_id)
            self.output = Matrix.empty(matrix.nrows, 1, matrix.dtype, device_id)
            self.alpha = None
        else:
            raise ValueError('Invalid axis!')
        self._ones.sync_fill(1.0)
        self.axis = axis

        if matrix.bpropagable:
            self.matrix, self.dL_dmatrix = matrix.register_usage(self.context, self.context)
            self.output = Connector(self.output, self.context, self.context)
        else:
            self.matrix = matrix.register_usage(self.context)
            self.output = Connector(self.output, self.context)

    def fprop(self):
        if self.axis == 0:
            self.output.ncols = self.matrix.ncols
            self.output.add_dot(self.context, self._ones, self.matrix, alpha=self.alpha, beta=self._zero)
        else:
            self._ones.nrows = self.matrix.ncols
            self.alpha = self._ctype(1.0 / self.matrix.ncols)
            self.output.add_dot(self.context, self.matrix, self._ones, alpha=self.alpha, beta=self._zero)
        self.output.fprop()

    def bprop(self):
        dL_doutput = self.output.backward_matrix
        dL_doutput.scale(self.context, self.alpha)
        if hasattr(self, 'dL_dmatrix'):
            self.dL_dmatrix.tile(self.context, self.axis, dL_doutput)