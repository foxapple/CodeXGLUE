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
import ctypes as ct
from quagga.cuda import cudart


gpu_matrix_kernels = ct.cdll.LoadLibrary('gpu_matrix_kernels.so')


gpu_matrix_kernels._scale.restype = cudart.ct_cuda_error
gpu_matrix_kernels._scale.argtypes = [cudart.ct_cuda_stream,
                                      ct.c_int,
                                      ct.c_float,
                                      ct.POINTER(ct.c_float),
                                      ct.POINTER(ct.c_float)]
def scale(stream, nelems, alpha, data, out_data):
    status = gpu_matrix_kernels._scale(stream, nelems, alpha, data, out_data)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._fill.restype = cudart.ct_cuda_error
gpu_matrix_kernels._fill.argtypes = [cudart.ct_cuda_stream,
                                     ct.c_int,
                                     ct.c_float,
                                     ct.POINTER(ct.c_float)]
def fill(stream, nelems, value, out_data):
    status = gpu_matrix_kernels._fill(stream, nelems, value, out_data)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._maskedFill.restype = cudart.ct_cuda_error
gpu_matrix_kernels._maskedFill.argtypes = [cudart.ct_cuda_stream,
                                           ct.c_int,
                                           ct.c_float,
                                           ct.POINTER(ct.c_float),
                                           ct.c_float,
                                           ct.POINTER(ct.c_float)]
def masked_fill(stream, nelems, value, mask_data, true_value, out_data):
    status = gpu_matrix_kernels.\
        _maskedFill(stream, nelems, value, mask_data, true_value, out_data)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._add_sum.restype = cudart.ct_cuda_error
gpu_matrix_kernels._add_sum.argtypes = [cudart.ct_cuda_stream,
                                        ct.c_int,
                                        ct.POINTER(ct.POINTER(ct.c_float)),
                                        ct.c_int,
                                        ct.POINTER(ct.c_float)]
def add_sum(stream, nelems, matrices, n, s):
    status = gpu_matrix_kernels._add_sum(stream, nelems, matrices, n, s)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assign_sum.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assign_sum.argtypes = [cudart.ct_cuda_stream,
                                           ct.c_int,
                                           ct.POINTER(ct.POINTER(ct.c_float)),
                                           ct.c_int,
                                           ct.POINTER(ct.c_float)]
def assign_sum(stream, nelems, matrices, n, s):
    status = gpu_matrix_kernels._assign_sum(stream, nelems, matrices, n, s)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addScaledColumnsSlice.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addScaledColumnsSlice.argtypes = [cudart.ct_cuda_stream,
                                                      ct.c_int,
                                                      ct.c_int,
                                                      ct.c_float,
                                                      ct.POINTER(ct.c_float),
                                                      ct.POINTER(ct.c_int),
                                                      ct.POINTER(ct.c_float)]
def add_scaled_columns_slice(stream, nrows, ncols, alpha, dense_matrix, embedding_column_indxs, embedding_matrix):
    status = gpu_matrix_kernels._addScaledColumnsSlice(stream, nrows, ncols, alpha, dense_matrix, embedding_column_indxs, embedding_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addScaledRowsSlice.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addScaledRowsSlice.argtypes = [cudart.ct_cuda_stream,
                                                   ct.c_int,
                                                   ct.c_int,
                                                   ct.c_float,
                                                   ct.POINTER(ct.c_float),
                                                   ct.POINTER(ct.c_int),
                                                   ct.c_int,
                                                   ct.POINTER(ct.c_float)]
def add_scaled_rows_slice(stream, nrows, ncols, alpha, dense_matrix, embedding_row_indxs, embd_nrows, embedding_matrix):
    status = gpu_matrix_kernels._addScaledRowsSlice(stream, nrows, ncols, alpha, dense_matrix, embedding_row_indxs, embd_nrows, embedding_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addHadamardProduct2.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addHadamardProduct2.argtypes = [cudart.ct_cuda_stream,
                                                    ct.c_int,
                                                    ct.POINTER(ct.c_float),
                                                    ct.POINTER(ct.c_float),
                                                    ct.c_float,
                                                    ct.POINTER(ct.c_float)]
def add_hadamard_product_2(stream, nelems, a, b, alpha, c):
    status = gpu_matrix_kernels._addHadamardProduct2(stream, nelems, a, b, alpha, c)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addHadamardProduct3.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addHadamardProduct3.argtypes = [cudart.ct_cuda_stream,
                                                    ct.c_int,
                                                    ct.POINTER(ct.c_float),
                                                    ct.POINTER(ct.c_float),
                                                    ct.POINTER(ct.c_float),
                                                    ct.c_float,
                                                    ct.POINTER(ct.c_float)]
def add_hadamard_product_3(stream, nelems, a, b, c, alpha, d):
    status = gpu_matrix_kernels._addHadamardProduct3(stream, nelems, a, b, c, alpha, d)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addScaledHadamardProduct.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addScaledHadamardProduct.argtypes = [cudart.ct_cuda_stream,
                                                         ct.c_int,
                                                         ct.POINTER(ct.c_float),
                                                         ct.POINTER(ct.c_float),
                                                         ct.c_float,
                                                         ct.c_float,
                                                         ct.POINTER(ct.c_float)]
def add_scaled_hadamard_product(stream, nelems, a, b, alpha, beta, c):
    status = gpu_matrix_kernels._addScaledHadamardProduct(stream, nelems, a, b, alpha, beta, c)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._hadamardProduct2.restype = cudart.ct_cuda_error
gpu_matrix_kernels._hadamardProduct2.argtypes = [cudart.ct_cuda_stream,
                                                 ct.c_int,
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float)]
def hadamard_product_2(stream, nelems, a, b, c):
    status = gpu_matrix_kernels._hadamardProduct2(stream, nelems, a, b, c)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._hadamardProduct3.restype = cudart.ct_cuda_error
gpu_matrix_kernels._hadamardProduct3.argtypes = [cudart.ct_cuda_stream,
                                                 ct.c_int,
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float)]
def hadamard_product_3(stream, nelems, a, b, c, d):
    status = gpu_matrix_kernels._hadamardProduct3(stream, nelems, a, b, c, d)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sumHprod4.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sumHprod4.argtypes = [cudart.ct_cuda_stream,
                                          ct.c_int,
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float)]
def sum_hprod_4(stream, nelems, a, b, c, d, e):
    status = gpu_matrix_kernels._sumHprod4(stream, nelems, a, b, c, d, e)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sumHprod5.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sumHprod5.argtypes = [cudart.ct_cuda_stream,
                                          ct.c_int,
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float)]
def sum_hprod_5(stream, nelems, a, b, c, d, e, f):
    status = gpu_matrix_kernels._sumHprod5(stream, nelems, a, b, c, d, e, f)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sumHprod11.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sumHprod11.argtypes = [cudart.ct_cuda_stream,
                                           ct.c_int,
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float),
                                           ct.POINTER(ct.c_float)]
def sum_hprod_11(stream, nelems, a, b, c, d, e, f, g, h, i, j, k, l):
    status = gpu_matrix_kernels._sumHprod11(stream, nelems, a, b, c, d, e, f, g, h, i, j, k, l)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._columnArgmax.restype = cudart.ct_cuda_error
gpu_matrix_kernels._columnArgmax.argtypes = [cudart.ct_cuda_stream,
                                             ct.c_int,
                                             ct.c_int,
                                             ct.POINTER(ct.c_float),
                                             ct.POINTER(ct.c_int)]
def column_argmax(stream, nrows, ncols, a, indxs):
    status = gpu_matrix_kernels._columnArgmax(stream, nrows, ncols, a, indxs)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._hprodSum.restype = cudart.ct_cuda_error
gpu_matrix_kernels._hprodSum.argtypes = [cudart.ct_cuda_stream,
                                         ct.c_int,
                                         ct.c_int,
                                         ct.POINTER(ct.c_float),
                                         ct.POINTER(ct.c_float),
                                         ct.POINTER(ct.c_float)]
def hprod_sum(stream, nrows, ncols, a, b, c):
    status = gpu_matrix_kernels._hprodSum(stream, nrows, ncols, a, b, c)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sliceColumns.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sliceColumns.argtypes = [cudart.ct_cuda_stream,
                                             ct.c_int,
                                             ct.c_int,
                                             ct.POINTER(ct.c_int),
                                             ct.POINTER(ct.c_float),
                                             ct.POINTER(ct.c_float)]
def slice_columns(stream, nrows, ncols, embedding_column_indxs, embedding_matrix, dense_matrix):
    status = gpu_matrix_kernels._sliceColumns(stream, nrows, ncols, embedding_column_indxs, embedding_matrix, dense_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sliceColumnsAndTranspose.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sliceColumnsAndTranspose.argtypes = [cudart.ct_cuda_stream,
                                                         ct.c_int,
                                                         ct.c_int,
                                                         ct.POINTER(ct.c_int),
                                                         ct.POINTER(ct.c_float),
                                                         ct.POINTER(ct.c_float)]
def slice_columns_and_transpose(stream, nrows, ncols, embedding_column_indxs, embedding_matrix, dense_matrix):
    status = gpu_matrix_kernels._sliceColumnsAndTranspose(stream, nrows, ncols, embedding_column_indxs, embedding_matrix, dense_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sliceRowsFloat.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sliceRowsFloat.argtypes = [cudart.ct_cuda_stream,
                                               ct.c_int,
                                               ct.POINTER(ct.c_int),
                                               ct.POINTER(ct.c_float),
                                               ct.c_int,
                                               ct.c_int,
                                               ct.POINTER(ct.c_float)]
def slice_rows_float(stream, embedding_matrix_nrows, embedding_row_indxs, embedding_matrix, nrows, ncols, dense_matrix):
    status = gpu_matrix_kernels._sliceRowsFloat(stream, embedding_matrix_nrows, embedding_row_indxs, embedding_matrix, nrows, ncols, dense_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sliceRowsInt.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sliceRowsInt.argtypes = [cudart.ct_cuda_stream,
                                             ct.c_int,
                                             ct.POINTER(ct.c_int),
                                             ct.POINTER(ct.c_int),
                                             ct.c_int,
                                             ct.c_int,
                                             ct.POINTER(ct.c_int)]
def slice_rows_int(stream, embedding_matrix_nrows, embedding_row_indxs, embedding_matrix, nrows, ncols, dense_matrix):
    status = gpu_matrix_kernels._sliceRowsInt(stream, embedding_matrix_nrows, embedding_row_indxs, embedding_matrix, nrows, ncols, dense_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._verticalStack.restype = cudart.ct_cuda_error
gpu_matrix_kernels._verticalStack.argtypes = [cudart.ct_cuda_stream,
                                              ct.c_int,
                                              ct.POINTER(ct.c_int),
                                              ct.c_int,
                                              ct.POINTER(ct.POINTER(ct.c_float)),
                                              ct.POINTER(ct.c_float)]
def vertical_stack(stream, n, nrows, ncols, matrices, stacked):
    status = gpu_matrix_kernels._verticalStack(stream, n, nrows, ncols, matrices, stacked)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._horizontalStack.restype = cudart.ct_cuda_error
gpu_matrix_kernels._horizontalStack.argtypes = [cudart.ct_cuda_stream,
                                                ct.c_int,
                                                ct.POINTER(ct.c_int),
                                                ct.c_int,
                                                ct.POINTER(ct.POINTER(ct.c_float)),
                                                ct.POINTER(ct.c_float)]
def horizontal_stack(stream, n, ncols, nrows, matrices, stacked):
    status = gpu_matrix_kernels._horizontalStack(stream, n, ncols, nrows, matrices, stacked)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._verticalSplit.restype = cudart.ct_cuda_error
gpu_matrix_kernels._verticalSplit.argtypes = [cudart.ct_cuda_stream,
                                              ct.c_int,
                                              ct.POINTER(ct.c_int),
                                              ct.c_int,
                                              ct.POINTER(ct.POINTER(ct.c_float)),
                                              ct.POINTER(ct.c_float)]
def vertical_split(stream, n, nrows, ncols, matrices, stacked):
    status = gpu_matrix_kernels._verticalSplit(stream, n, nrows, ncols, matrices, stacked)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._horizontalSplit.restype = cudart.ct_cuda_error
gpu_matrix_kernels._horizontalSplit.argtypes = [cudart.ct_cuda_stream,
                                                ct.c_int,
                                                ct.POINTER(ct.c_int),
                                                ct.c_int,
                                                ct.POINTER(ct.POINTER(ct.c_float)),
                                                ct.POINTER(ct.c_float)]
def hotizontal_split(stream, n, ncols, nrows, matrices, stacked):
    status = gpu_matrix_kernels._horizontalSplit(stream, n, ncols, nrows, matrices, stacked)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._verticalSliceSplit.restype = cudart.ct_cuda_error
gpu_matrix_kernels._verticalSliceSplit.argtypes = [cudart.ct_cuda_stream,
                                                   ct.c_int,
                                                   ct.POINTER(ct.c_int),
                                                   ct.c_int,
                                                   ct.c_int,
                                                   ct.POINTER(ct.POINTER(ct.c_float)),
                                                   ct.POINTER(ct.c_float)]
def vertical_slice_split(stream, n, row_slices, nrows, ncols, matrices, stacked):
    status = gpu_matrix_kernels._verticalSliceSplit(stream, n, row_slices, nrows, ncols, matrices, stacked)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._horizontalSliceSplit.restype = cudart.ct_cuda_error
gpu_matrix_kernels._horizontalSliceSplit.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.POINTER(ct.c_int),
                                                     ct.c_int,
                                                     ct.POINTER(ct.POINTER(ct.c_float)),
                                                     ct.POINTER(ct.c_float)]
def horizontal_slice_split(stream, n, col_slices, nrows, matrices, stacked):
    status = gpu_matrix_kernels._horizontalSliceSplit(stream, n, col_slices, nrows, matrices, stacked)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._matrixVectorRowAddition.restype = cudart.ct_cuda_error
gpu_matrix_kernels._matrixVectorRowAddition.argtypes = [cudart.ct_cuda_stream,
                                                        ct.c_int,
                                                        ct.c_int,
                                                        ct.POINTER(ct.c_float),
                                                        ct.c_float,
                                                        ct.POINTER(ct.c_float),
                                                        ct.POINTER(ct.c_float)]
def matrix_vector_row_addition(stream, nrows, ncols, matrix, alpha, vector, out):
    status = gpu_matrix_kernels._matrixVectorRowAddition(stream, nrows, ncols, matrix, alpha, vector, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignSequentialMeanPooling.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignSequentialMeanPooling.argtypes = [cudart.ct_cuda_stream,
                                                            ct.c_int,
                                                            ct.c_int,
                                                            ct.POINTER(ct.POINTER(ct.c_float)),
                                                            ct.c_int,
                                                            ct.POINTER(ct.c_float)]
def assign_sequential_mean_pooling(stream, nrows, ncols, matrices, n, out):
    status = gpu_matrix_kernels._assignSequentialMeanPooling(stream, nrows, ncols, matrices, n, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignSequentialSumPooling.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignSequentialSumPooling.argtypes = [cudart.ct_cuda_stream,
                                                           ct.c_int,
                                                           ct.c_int,
                                                           ct.POINTER(ct.POINTER(ct.c_float)),
                                                           ct.c_int,
                                                           ct.POINTER(ct.c_float)]
def assign_sequential_sum_pooling(stream, nrows, ncols, matrices, n, out):
    status = gpu_matrix_kernels._assignSequentialSumPooling(stream, nrows, ncols, matrices, n, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignSequentialWeightedSum.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignSequentialWeightedSum.argtypes = [cudart.ct_cuda_stream,
                                                            ct.c_int,
                                                            ct.c_int,
                                                            ct.POINTER(ct.POINTER(ct.c_float)),
                                                            ct.POINTER(ct.c_float),
                                                            ct.c_int,
                                                            ct.POINTER(ct.c_float)]
def assign_sequential_weighted_sum(stream, nrows, ncols, matrices, weights, n, out):
    status = gpu_matrix_kernels._assignSequentialWeightedSum(stream, nrows, ncols, matrices, weights, n, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sequentiallyTile.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sequentiallyTile.argtypes = [cudart.ct_cuda_stream,
                                                 ct.c_int,
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.POINTER(ct.c_float)),
                                                 ct.c_int]
def sequentially_tile(stream, nelems, a, matrices, n):
    status = gpu_matrix_kernels._sequentiallyTile(stream, nelems, a, matrices, n)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignDLDprea.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignDLDprea.argtypes = [cudart.ct_cuda_stream,
                                              ct.c_int,
                                              ct.c_int,
                                              ct.POINTER(ct.POINTER(ct.c_float)),
                                              ct.POINTER(ct.c_float),
                                              ct.POINTER(ct.c_float),
                                              ct.c_int,
                                              ct.POINTER(ct.c_float)]
def assign_dL_dpre_a(stream, nrows, ncols, matrices, derivative, weights, n, out):
    status = gpu_matrix_kernels._assignDLDprea(stream, nrows, ncols, matrices, derivative, weights, n, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addAttentionDerivative.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addAttentionDerivative.argtypes = [cudart.ct_cuda_stream,
                                                       ct.c_int,
                                                       ct.c_int,
                                                       ct.POINTER(ct.POINTER(ct.c_float)),
                                                       ct.POINTER(ct.c_float),
                                                       ct.c_int,
                                                       ct.POINTER(ct.c_float)]
def add_attention_derivative(stream, nrows, ncols, matrices, derivative, n, out):
    status = gpu_matrix_kernels._addAttentionDerivative(stream, nrows, ncols, matrices, derivative, n, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addAttentionTile.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addAttentionTile.argtypes = [cudart.ct_cuda_stream,
                                                 ct.c_int,
                                                 ct.c_int,
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.c_int,
                                                 ct.POINTER(ct.POINTER(ct.c_float))]
def add_attention_tile(stream, nrows, ncols, derivative, a, dL_dpre_a, u, n, matrices_derivs):
    status = gpu_matrix_kernels._addAttentionTile(stream, nrows, ncols, derivative, a, dL_dpre_a, u, n, matrices_derivs)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._sliceRowsBatch.restype = cudart.ct_cuda_error
gpu_matrix_kernels._sliceRowsBatch.argtypes = [cudart.ct_cuda_stream,
                                               ct.POINTER(ct.c_int),
                                               ct.c_int,
                                               ct.c_int,
                                               ct.POINTER(ct.c_float),
                                               ct.c_int,
                                               ct.c_int,
                                               ct.POINTER(ct.POINTER(ct.c_float))]
def slice_rows_batch(stream, embd_rows_indxs, nrows, ncols, embd_matrix, embd_nrows, embd_ncols, dense_matrices):
    status = gpu_matrix_kernels._sliceRowsBatch(stream, embd_rows_indxs, nrows, ncols, embd_matrix, embd_nrows, embd_ncols, dense_matrices)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._slicedRowsBatchScaledAdd.restype = cudart.ct_cuda_error
gpu_matrix_kernels._slicedRowsBatchScaledAdd.argtypes = [cudart.ct_cuda_stream,
                                                         ct.POINTER(ct.c_int),
                                                         ct.c_int,
                                                         ct.c_int,
                                                         ct.c_float,
                                                         ct.POINTER(ct.POINTER(ct.c_float)),
                                                         ct.c_int,
                                                         ct.c_int,
                                                         ct.POINTER(ct.c_float)]
def sliced_rows_batch_scaled_add(stream, embd_rows_indxs, nrows, ncols, alpha, dense_matrices, embd_nrows, embd_ncols, embd_matrix):
    status = gpu_matrix_kernels._slicedRowsBatchScaledAdd(stream, embd_rows_indxs, nrows, ncols, alpha, dense_matrices, embd_nrows, embd_ncols, embd_matrix)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignScaledAddition.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignScaledAddition.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.c_float,
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float)]
def assign_scaled_addition(stream, nelems, alpha, a, b, out):
    status = gpu_matrix_kernels._assignScaledAddition(stream, nelems, alpha, a, b, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignScaledSubtraction.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignScaledSubtraction.argtypes = [cudart.ct_cuda_stream,
                                                        ct.c_int,
                                                        ct.c_float,
                                                        ct.POINTER(ct.c_float),
                                                        ct.POINTER(ct.c_float),
                                                        ct.POINTER(ct.c_float)]
def assign_scaled_subtraction(stream, nelems, alpha, a, b, out):
    status = gpu_matrix_kernels._assignScaledSubtraction(stream, nelems, alpha, a, b, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addScaledSubtraction.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addScaledSubtraction.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.c_float,
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float)]
def add_scaled_subtraction(stream, nelems, alpha, a, b, out):
    status = gpu_matrix_kernels._addScaledSubtraction(stream, nelems, alpha, a, b, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._softmaxCeDerivative.restype = cudart.ct_cuda_error
gpu_matrix_kernels._softmaxCeDerivative.argtypes = [cudart.ct_cuda_stream,
                                                    ct.c_int,
                                                    ct.c_int,
                                                    ct.POINTER(ct.c_float),
                                                    ct.POINTER(ct.c_int),
                                                    ct.POINTER(ct.c_float)]
def softmax_ce_derivative(stream, batchSize, num_classes, probs, target_classes, derivatives):
    status = gpu_matrix_kernels._softmaxCeDerivative(stream, batchSize, num_classes, probs, target_classes, derivatives)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addSoftmaxCeDerivative.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addSoftmaxCeDerivative.argtypes = [cudart.ct_cuda_stream,
                                                       ct.c_int,
                                                       ct.c_int,
                                                       ct.POINTER(ct.c_float),
                                                       ct.POINTER(ct.c_int),
                                                       ct.POINTER(ct.c_float)]
def add_softmax_ce_derivative(stream, batchSize, num_classes, probs, target_classes, derivatives):
    status = gpu_matrix_kernels._addSoftmaxCeDerivative(stream, batchSize, num_classes, probs, target_classes, derivatives)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._dropout.restype = cudart.ct_cuda_error
gpu_matrix_kernels._dropout.argtypes = [cudart.ct_cuda_stream,
                                        ct.c_int,
                                        ct.c_float,
                                        ct.POINTER(ct.c_float),
                                        ct.POINTER(ct.c_float),
                                        ct.POINTER(ct.c_float)]
def dropout(stream, nelems, dropout_prob, data, uniform_data, out):
    status = gpu_matrix_kernels._dropout(stream, nelems, dropout_prob, data, uniform_data, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._maskZeros.restype = cudart.ct_cuda_error
gpu_matrix_kernels._maskZeros.argtypes = [cudart.ct_cuda_stream,
                                          ct.c_int,
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float),
                                          ct.POINTER(ct.c_float)]
def mask_zeros(stream, nelems, a, b, out):
    status = gpu_matrix_kernels._maskZeros(stream, nelems, a, b, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addMaskZeros.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addMaskZeros.argtypes = [cudart.ct_cuda_stream,
                                             ct.c_int,
                                             ct.POINTER(ct.c_float),
                                             ct.POINTER(ct.c_float),
                                             ct.POINTER(ct.c_float)]
def add_mask_zeros(stream, nelems, a, b, out):
    status = gpu_matrix_kernels._addMaskZeros(stream, nelems, a, b, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._assignMaskedAddition.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignMaskedAddition.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float)]
def assign_masked_addition(stream, nelems, mask, a, b, out):
    status = gpu_matrix_kernels._assignMaskedAddition(stream, nelems, mask, a, b, out)
    cudart.check_cuda_status(status)



gpu_matrix_kernels._assignMaskedAdditionColumnBroadcasted.restype = cudart.ct_cuda_error
gpu_matrix_kernels._assignMaskedAdditionColumnBroadcasted.argtypes = [cudart.ct_cuda_stream,
                                                                      ct.c_int,
                                                                      ct.c_int,
                                                                      ct.POINTER(ct.c_float),
                                                                      ct.POINTER(ct.c_float),
                                                                      ct.POINTER(ct.c_float),
                                                                      ct.POINTER(ct.c_float)]
def assign_masked_addition_column_broadcasted(stream, nrows, ncols, mask, a, b, out):
    status = gpu_matrix_kernels._assignMaskedAdditionColumnBroadcasted(stream, nrows, ncols, mask, a, b, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addHprodOneMinusMask.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addHprodOneMinusMask.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float),
                                                     ct.POINTER(ct.c_float)]
def add_hprod_one_minus_mask(stream, nelems, mask, a, out):
    status = gpu_matrix_kernels._addHprodOneMinusMask(stream, nelems, mask, a, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addHprodOneMinusMaskColumnBroadcasted.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addHprodOneMinusMaskColumnBroadcasted.argtypes = [cudart.ct_cuda_stream,
                                                                      ct.c_int,
                                                                      ct.c_int,
                                                                      ct.POINTER(ct.c_float),
                                                                      ct.POINTER(ct.c_float),
                                                                      ct.POINTER(ct.c_float)]
def add_hprod_one_minus_mask_column_broadcasted(stream, nrows, ncols, mask, a, out):
    status = gpu_matrix_kernels._addHprodOneMinusMaskColumnBroadcasted(stream, nrows, ncols, mask, a, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._matrixVectorColumnHprod.restype = cudart.ct_cuda_error
gpu_matrix_kernels._matrixVectorColumnHprod.argtypes = [cudart.ct_cuda_stream,
                                                        ct.c_int,
                                                        ct.c_int,
                                                        ct.POINTER(ct.c_float),
                                                        ct.POINTER(ct.c_float),
                                                        ct.POINTER(ct.c_float)]
def matrix_vector_column_hprod(stream, nrows, ncols, matrix, vector, out):
    status = gpu_matrix_kernels._matrixVectorColumnHprod(stream, nrows, ncols, matrix, vector, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._maskColumnNumbersRowWise.restype = cudart.ct_cuda_error
gpu_matrix_kernels._maskColumnNumbersRowWise.argtypes = [cudart.ct_cuda_stream,
                                                         ct.c_int,
                                                         ct.c_int,
                                                         ct.POINTER(ct.c_int),
                                                         ct.POINTER(ct.c_float)]
def mask_column_numbers_row_wise(stream, nrows, ncols, numbers, out):
    status = gpu_matrix_kernels._maskColumnNumbersRowWise(stream, nrows, ncols, numbers, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._batchHorizontalStack.restype = cudart.ct_cuda_error
gpu_matrix_kernels._batchHorizontalStack.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.c_int,
                                                     ct.c_int,
                                                     ct.c_int,
                                                     ct.POINTER(ct.POINTER(ct.c_float)),
                                                     ct.POINTER(ct.POINTER(ct.c_float)),
                                                     ct.POINTER(ct.POINTER(ct.c_float))]
def batch_horizontal_stack(stream, n, nrows, x_ncols, y_ncols, x_matrices, y_matrices, out_matrices):
    status = gpu_matrix_kernels._batchHorizontalStack(stream, n, nrows, x_ncols, y_ncols, x_matrices, y_matrices, out_matrices)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._batchHorizontalSplit.restype = cudart.ct_cuda_error
gpu_matrix_kernels._batchHorizontalSplit.argtypes = [cudart.ct_cuda_stream,
                                                     ct.c_int,
                                                     ct.c_int,
                                                     ct.c_int,
                                                     ct.c_int,
                                                     ct.POINTER(ct.POINTER(ct.c_float)),
                                                     ct.POINTER(ct.POINTER(ct.c_float)),
                                                     ct.POINTER(ct.POINTER(ct.c_float))]
def batch_horizontal_split(stream, n, nrows, x_ncols, y_ncols, matrices, x_matrices, y_matrices):
    status = gpu_matrix_kernels._batchHorizontalSplit(stream, n, nrows, x_ncols, y_ncols, matrices, x_matrices, y_matrices)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._repeatAlongRow.restype = cudart.ct_cuda_error
gpu_matrix_kernels._repeatAlongRow.argtypes = [cudart.ct_cuda_stream,
                                               ct.c_int,
                                               ct.c_int,
                                               ct.c_int,
                                               ct.POINTER(ct.c_float),
                                               ct.POINTER(ct.c_float)]
def repeat_along_row(stream, repeats, nrows, ncols, a, out):
    status = gpu_matrix_kernels._repeatAlongRow(stream, repeats, nrows, ncols, a, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addRepeatAlongRowDerivative.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addRepeatAlongRowDerivative.argtypes = [cudart.ct_cuda_stream,
                                                            ct.c_int,
                                                            ct.POINTER(ct.c_float),
                                                            ct.c_int,
                                                            ct.c_int,
                                                            ct.POINTER(ct.c_float)]
def add_repeat_along_row_derivative(stream, repeats, a, nrows, ncols, derivative):
    status = gpu_matrix_kernels._addRepeatAlongRowDerivative(stream, repeats, a, nrows, ncols, derivative)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._repeatAlongCol.restype = cudart.ct_cuda_error
gpu_matrix_kernels._repeatAlongCol.argtypes = [cudart.ct_cuda_stream,
                                               ct.c_int,
                                               ct.c_int,
                                               ct.c_int,
                                               ct.POINTER(ct.c_float),
                                               ct.POINTER(ct.c_float)]
def repeat_along_col(stream, repeats, nrows, ncols, a, out):
    status = gpu_matrix_kernels._repeatAlongCol(stream, repeats, nrows, ncols, a, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addRepeatAlongColDerivative.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addRepeatAlongColDerivative.argtypes = [cudart.ct_cuda_stream,
                                                            ct.c_int,
                                                            ct.POINTER(ct.c_float),
                                                            ct.c_int,
                                                            ct.c_int,
                                                            ct.POINTER(ct.c_float)]
def add_repeat_along_col_derivative(stream, repeats, a, nrows, ncols, derivative):
    status = gpu_matrix_kernels._addRepeatAlongColDerivative(stream, repeats, a, nrows, ncols, derivative)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._addScaledDivSqrt.restype = cudart.ct_cuda_error
gpu_matrix_kernels._addScaledDivSqrt.argtypes = [cudart.ct_cuda_stream,
                                                 ct.c_int,
                                                 ct.c_float,
                                                 ct.POINTER(ct.c_float),
                                                 ct.POINTER(ct.c_float),
                                                 ct.c_float,
                                                 ct.POINTER(ct.c_float)]
def add_scaled_div_sqrt(stream, nelems, alpha, a, b, epsilon, c):
    status = gpu_matrix_kernels._addScaledDivSqrt(stream, nelems, alpha, a, b, epsilon, c)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._clip.restype = cudart.ct_cuda_error
gpu_matrix_kernels._clip.argtypes = [cudart.ct_cuda_stream,
                                     ct.c_int,
                                     ct.c_float,
                                     ct.c_float,
                                     ct.POINTER(ct.c_float),
                                     ct.POINTER(ct.c_float)]
def clip(stream, nelems, min_value, max_value, data, out):
    status = gpu_matrix_kernels._clip(stream, nelems, min_value, max_value, data, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._transposeFloat.restype = cudart.ct_cuda_error
gpu_matrix_kernels._transposeFloat.argtypes = [cudart.ct_cuda_stream,
                                               ct.c_int,
                                               ct.c_int,
                                               ct.POINTER(ct.c_float),
                                               ct.POINTER(ct.c_float)]
def transpose_float(stream, nrows, ncols, in_, out):
    status = gpu_matrix_kernels._transposeFloat(stream, nrows, ncols, in_, out)
    cudart.check_cuda_status(status)


gpu_matrix_kernels._transposeInt.restype = cudart.ct_cuda_error
gpu_matrix_kernels._transposeInt.argtypes = [cudart.ct_cuda_stream,
                                             ct.c_int,
                                             ct.c_int,
                                             ct.POINTER(ct.c_int),
                                             ct.POINTER(ct.c_int)]
def transpose_int(stream, nrows, ncols, in_, out):
    status = gpu_matrix_kernels._transposeInt(stream, nrows, ncols, in_, out)
    cudart.check_cuda_status(status)