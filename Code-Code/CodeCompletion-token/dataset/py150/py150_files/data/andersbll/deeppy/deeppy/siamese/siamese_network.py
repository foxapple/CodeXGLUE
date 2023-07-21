from copy import copy
import numpy as np
from ..base import Model, CollectionMixin, ParamMixin
from ..feed import Feed


class SiameseNetwork(Model, CollectionMixin):
    def __init__(self, siamese_layers, loss):
        self.layers = siamese_layers
        self.loss = loss
        # Create second array of layers
        self.layers2 = [copy(layer) for layer in self.layers]
        for layer1, layer2 in zip(self.layers, self.layers2):
            if isinstance(layer1, ParamMixin):
                # Replace weights in layers2 with shared weights
                layer2.params = [p.share() for p in layer1.params]
        self.bprop_until = next((idx for idx, l in enumerate(self.layers)
                                 if isinstance(l, ParamMixin)), 0)
        self.layers[self.bprop_until].bprop_to_x = False
        self.layers2[self.bprop_until].bprop_to_x = False
        self.collection = self.layers + self.layers2
        self._initialized = False

    def setup(self, x1_shape, x2_shape, y_shape=None):
        # Setup layers sequentially
        if self._initialized:
            return
        next_shape = x1_shape
        for layer in self.layers:
            layer.setup(next_shape)
            next_shape = layer.y_shape(next_shape)
        next_shape = x2_shape
        for layer in self.layers2:
            layer.setup(next_shape)
            next_shape = layer.y_shape(next_shape)
        next_shape = self.loss.y_shape(next_shape)
        self._initialized = True

    def update(self, x1, x2, y):
        self.phase = 'train'

        # Forward propagation
        for layer in self.layers:
            x1 = layer.fprop(x1)
        for layer in self.layers2:
            x2 = layer.fprop(x2)

        # Back propagation of partial derivatives
        grad1, grad2 = self.loss.grad(y, x1, x2)
        layers = self.layers[self.bprop_until:]
        for layer in reversed(layers[1:]):
            grad1 = layer.bprop(grad1)
        layers[0].bprop(grad1)

        layers2 = self.layers2[self.bprop_until:]
        for layer in reversed(layers2[1:]):
            grad2 = layer.bprop(grad2)
        layers2[0].bprop(grad2)

        return self.loss.loss(y, x1, x2)

    def embed(self, feed):
        self.phase = 'test'
        feed = Feed.from_any(feed)
        next_shape = feed.x.shape
        for layer in self.layers:
            next_shape = layer.y_shape(next_shape)
        feats = []
        for x, in feed.batches():
            for layer in self.layers:
                x = layer.fprop(x)
            feats.append(np.array(x))
        feats = np.concatenate(feats)[:feed.n_samples]
        return feats

    def distances(self, feed):
        self.phase = 'test'
        feed = Feed.from_any(feed)
        dists = []
        for x1, x2 in feed.batches():
            for layer in self.layers:
                x1 = layer.fprop(x1)
            for layer in self.layers2:
                x2 = layer.fprop(x2)
            dists.append(np.ravel(np.array(self.loss.fprop(x1, x2))))
        dists = np.concatenate(dists)[:feed.n_samples]
        return dists
