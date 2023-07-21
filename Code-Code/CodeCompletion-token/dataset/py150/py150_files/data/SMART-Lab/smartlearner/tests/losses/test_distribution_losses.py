import numpy as np
import theano.tensor as T

from numpy.testing import assert_equal
from smartlearner.testing import DummyDataset, DummyModel

from smartlearner.interfaces import Loss
from smartlearner.losses.distribution_losses import BinaryCrossEntropy


def test_binary_cross_entropy():
    batch_size = 13
    input_dim = 32

    rng = np.random.RandomState(42)
    targets = (rng.rand(batch_size, input_dim) > 0.5).astype(np.float32)

    dataset = DummyDataset()
    dataset.symb_targets = targets

    loss = BinaryCrossEntropy(DummyModel(), dataset)
    model_output = rng.rand(batch_size, input_dim).astype(np.float32)

    # Test the shape of the output of _compute_losses.
    losses = loss._compute_losses(model_output).eval()
    assert_equal(losses.shape, (batch_size, ))
