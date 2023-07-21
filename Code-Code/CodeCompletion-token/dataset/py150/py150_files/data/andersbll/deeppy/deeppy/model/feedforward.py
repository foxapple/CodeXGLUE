import numpy as np
import cudarray as ca
from ..base import Model, CollectionMixin, PickleMixin
from ..feed import Feed
from .. import expr as ex


class FeedForwardNet(Model, CollectionMixin, PickleMixin):
    _pickle_ignore = ['graph']

    def __init__(self, expression, loss):
        self.expression = expression
        self.loss = loss
        self.graph = None
        self.collection = [expression]

    def setup(self, x_shape, y_shape=None):
        self.x_src = ex.Source(x_shape)
        y_expr = self._fprop_expr(self.x_src)
        if y_shape is not None:
            self.y_src = ex.Source(y_shape)
            y_expr = self.loss(y_expr, self.y_src)
            y_expr.grad_array = ca.array(1.0)
        self.graph = ex.graph.ExprGraph(y_expr)
        self.graph.setup()

    def _fprop_expr(self, x):
        return self.expression(x)

    def update(self, x, y):
        self.x_src.array = x
        self.y_src.array = y
        self.graph.fprop()
        self.graph.bprop()
        return self.loss.array

    def _batchwise(self, feed, expr_fun):
        feed = Feed.from_any(feed)
        src = ex.Source(feed.x_shape)
        sink = expr_fun(src)
        graph = ex.graph.ExprGraph(sink)
        graph.setup()
        y = []
        for x, in feed.batches():
            src.array = x
            graph.fprop()
            y.append(np.array(sink.array))
        y = np.concatenate(y)[:feed.n_samples]
        return y

    def predict(self, feed):
        """ Calculate the output for the given input. """
        return self._batchwise(feed, self._fprop_expr)


class ClassifierNet(FeedForwardNet):
    def _fprop_expr(self, x):
        y_expr = super(ClassifierNet, self)._fprop_expr(x)
        if isinstance(self.loss, ex.nnet.SoftmaxCrossEntropy) and \
           not isinstance(y_expr, ex.nnet.Softmax):
            y_expr = ex.nnet.Softmax()(y_expr)
        return y_expr

    def _predict_expr(self, x):
        y_expr = self._fprop_expr(x)
        y_expr = ex.nnet.one_hot.OneHotDecode()(y_expr)
        return y_expr

    def predict(self, feed):
        """ Calculate the output for the given input. """
        return self._batchwise(feed, self._predict_expr)

    def predict_proba(self, feed):
        """ Calculate the output probabilities for the given input. """
        return self._batchwise(feed, self._fprop_expr)


class RegressorNet(FeedForwardNet):
    def predict(self, feed):
        """ Calculate the output for the given input. """
        return self._batchwise(feed, self._fprop_expr)
