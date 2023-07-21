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
import numpy as np
from quagga.matrix import Matrix
from quagga.context import Context
from quagga.connector import Connector


class SigmoidCeBlock(object):
    """
    Sigmoid nonlinearity with mean cross entropy loss
    """

    def __init__(self, x, true_labels, mask=None, device_id=None):
        self.context = Context(device_id)
        device_id = self.context.device_id
        if x.bpropagable:
            self.x, self.dL_dx = x.register_usage(device_id, device_id)
        else:
            self.x = x.register_usage(device_id)
        self.true_labels = true_labels.register_usage(device_id)
        if mask:
            self.mask = mask.register_usage(device_id)
        self.probs = Connector(Matrix.empty_like(self.x))
        self.loss = None

    def fprop(self):
        self.x.sigmoid(self.context, self.probs)
        self.probs.fprop()

    def bprop(self):
        # error = (probs - true_labels) / M
        self.dL_dx.add_scaled_subtraction(self.context,
                                          1. / float(self.probs.nrows),
                                          self.probs, self.true_labels)
        if hasattr(self, 'mask'):
            self.dL_dx.hprod(self.context, self.mask)

    def calculate_loss(self, context):
        true_labels_np = self.true_labels.to_host(context)
        probs_np = self.probs.to_host(context)
        if hasattr(self, 'mask'):
            mask = self.mask.to_host(context)
            context.add_callback(self._calculate_ce_loss,
                                 true_labels_np, probs_np, mask)
        else:
            context.add_callback(self._calculate_ce_loss,
                                 true_labels_np, probs_np)

    def _calculate_ce_loss(self, true_labels_np, probs_np, mask=None):
        logs = true_labels_np * np.log(probs_np + 1e-20) + \
               (1.0 - true_labels_np) * np.log(1. - probs_np + 1e-20)
        if mask is not None:
            logs *= mask
            self.loss = - np.sum(logs) / (np.sum(mask) * logs.shape[1])
        else:
            self.loss = - np.mean(logs)