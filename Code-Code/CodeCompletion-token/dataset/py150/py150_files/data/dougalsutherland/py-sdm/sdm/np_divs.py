#!/usr/bin/env python
'''
Script to run nonparametric divergence estimation via k-nearest-neighbor
distances. Based on the method of
    Barnabas Poczos, Liang Xiong, Jeff Schneider (2011).
    Nonparametric divergence estimation with applications to machine learning
    on distributions.
    Uncertainty in Artificial Intelligence.
    http://autonlab.org/autonweb/20287.html
'''

from __future__ import division, print_function

import argparse
from collections import namedtuple, defaultdict, OrderedDict
from functools import partial
import itertools
from operator import itemgetter
import os
import sys
import warnings

import numpy as np
import scipy.io
from scipy.special import gamma, gammaln, psi

from cyflann import FLANNIndex, FLANNParameters

from .features import Features
from .utils import (eps, izip, lazy_range, strict_map, raw_input, identity,
                    str_types, bytes, positive_int, confirm_outfile,
                    is_integer_type,
                    read_cell_array,
                    iteritems, itervalues, get_status_fn)
from .mp_utils import progress
from .knn_search import default_min_dist, pick_flann_algorithm
from ._np_divs import _linear, kl, _alpha_div, _jensen_shannon_core

try:
    from ._np_divs_cy import _estimate_cross_divs
except ImportError as e:
    msg = ("Cythonned divergence estimator not available, using the slow "
           "pure-Python version:\n{}".format(e))
    warnings.warn(msg)
    from ._np_divs import _estimate_cross_divs


################################################################################
### Estimators of various divergences based on nearest-neighbor distances.
#
# The standard interface for these functions is:
#
# Function attributes:
#
#   needs_alpha: whether this function needs an alpha parameter. Default false.
#
#   self_value: The value that this function should take when comparing a
#               sample to itself: either a scalar constant or None (the
#               default), in which case the function is still called with
#               rhos = nus.
#
#   chooser_fn: a function that gets alphas (if needs_alpha), Ks, dim, and ns
#               (the array of bag sizes) and returns a partial() of a "core"
#               function, with some things precomputed. If not present, just
#               does partial(fn, [alphas,] Ks, dim).
#
#   needs_all_ks: whether this function needs *all* the neighbor distances up
#                 to the max K value, rather than just the values of K that are
#                 actually used. Default false.
#
#   chooser_fn.returns_ks: whether the chooser_fn returns the max value of K
#                          needed. This allows an estimator function to require
#                          a higher value of K than requested by the user. Only
#                          if needs_all_ks; default false.
#
# Arguments:
#
#   alphas (if needs_alpha; array-like, scalar or 1d): the alpha values to use
#
#   Ks (array-like, scalar or 1d): the K values used
#
#   dim (scalar): the dimension of the feature space
#
#   num_q (scalar): the number of points in the sample from q
#
#   rhos: an array of within-bag nearest neighbor distances for a sample from p.
#         rhos[i, j] should be the distance from the ith sample from p to its
#         Ks[j]'th neighbor in the same sample. Shape: (num_p, num_Ks).
#   nus: an array of nearest neighbor distances from samples from other dists.
#        nus[i, j] should be the distance from the ith sample from p to its
#        Ks[j]'th neighbor in the sample from q. Shape: (num_p, num_Ks).
#
# Returns an array of divergence estimates. If needs_alpha, should be of shape
# (num_alphas, num_Ks); otherwise, of shape (num_Ks,).

def linear(Ks, dim, num_q, rhos, nus):
    r'''
    Estimates the linear inner product \int p q between two distributions,
    based on kNN distances.
    '''
    return _get_linear(Ks, dim)(num_q, rhos, nus)

def _get_linear(Ks, dim, ns=None):
    # Estimated with alpha=0, beta=1:
    #   B_{k,d,0,1} = (k - 1) / pi^(dim/2) * gamma(dim/2 + 1)
    #   (using gamma(k) / gamma(k - 1) = k - 1)
    Ks = np.reshape(Ks, (-1,))
    Bs = (Ks - 1) / np.pi ** (dim / 2) * gamma(dim / 2 + 1)  # shape (num_Ks,)
    return partial(_linear, Bs, dim)
linear.self_value = None  # have to execute it
linear.needs_alpha = False
linear.chooser_fn = _get_linear

# kl function is entirely in _np_divs (nothing to precompute)

def alpha_div(alphas, Ks, dim, num_q, rhos, nus):
    r'''
    Estimate the alpha divergence between distributions:
        \int p^\alpha q^(1-\alpha)
    based on kNN distances.

    Used in Renyi, Hellinger, Bhattacharyya, Tsallis divergences.

    Enforces that estimates are >= 0.

    Returns divergence estimates with shape (num_alphas, num_Ks).
    '''
    return _get_alpha_div(alphas, Ks, dim)(num_q, rhos, nus)

def _get_alpha_div(alphas, Ks, dim, ns=None):
    alphas = np.reshape(alphas, (-1, 1))
    Ks = np.reshape(Ks, (1, -1))

    omas = 1 - alphas

    # We're estimating with alpha = alpha-1, beta = 1-alpha.
    # B constant in front:
    #   estimator's alpha = -beta, so volume of unit ball cancels out
    #   and then ratio of gamma functions
    Bs = np.exp(gammaln(Ks) * 2 - gammaln(Ks + omas) - gammaln(Ks - omas))

    return partial(_alpha_div, omas, Bs, dim)

alpha_div.self_value = 1
alpha_div.needs_alpha = True
alpha_div.chooser_fn = _get_alpha_div


def jensen_shannon_core(Ks, dim, num_q, rhos, nus):
    r'''
    Estimates
          1/2 mean_X( d * log radius of largest ball in X+Y around X_i
                                with no more than M/(n+m-1) weight
                                where X points have weight 1 / (2 n - 1)
                                  and Y points have weight n / (m (2 n - 1))
                      - digamma(# of neighbors in that ball))

    This is the core pairwise component of the estimator of Jensen-Shannon
    divergence based on the Hino-Murata weighted information estimator. See
    the docstring for jensen_shannon for an explanation.
    '''
    ns = np.array([rhos.shape[0], num_q])
    return _get_jensen_shannon_core(Ks, dim, ns)[0](num_q, rhos, nus)

def _get_jensen_shannon_core(Ks, dim, ns):
    # precompute the max/min possible digamma(i) values: the floors/ceils of
    #
    #   M/(n+m-1) / (1 / (2 n - 1))
    #   M/(n+m-1) / (n / (m (2 n - 1)))
    #
    # for any valid value of n, m.

    min_n = np.min(ns)
    max_n = np.max(ns)

    min_K = np.min(Ks)
    max_K = np.max(Ks)

    # TODO: could probably math this out a bit more.
    # TODO: are these bounds wrong?????
    i_bounds = [np.inf, -np.inf]
    def add_i(i):
        if i < i_bounds[0]:
            i_bounds[0] = i
        if i > i_bounds[1]:
            i_bounds[1] = i

    for n in [max_n, min_n]:
        for m in [max_n, min_n]:
            base = (2 * n - 1) / (n + m - 1)
            for M in [max_K, min_K]:
                add_i(base * M)
                add_i(base * M * (m / n))
    min_i = int(np.floor(i_bounds[0]))
    if min_i <= 0:
        raise ValueError("have i = 0 possible; K is too small...")
    digamma_vals = psi(np.arange(min_i, int(np.ceil(i_bounds[1]) + 1)))

    return partial(_jensen_shannon_core, Ks, dim, min_i, digamma_vals), max_K

jensen_shannon_core.needs_alpha = False
jensen_shannon_core.chooser_fn = _get_jensen_shannon_core
jensen_shannon_core.needs_all_ks = True
jensen_shannon_core.chooser_fn.returns_ks = True
jensen_shannon_core.self_value = np.nan
# Obviously, the self_value should be the entropy estimate. But since we'll
# just subtract that later, don't bother computing it.


################################################################################
### Meta-estimators: things that need some additional computation on top of
###                  the per-bag stuff of the functions above.

# These functions are run after the base estimators above are complete.
#
# The interface here is:
#
# Function attributes:
#
#   needs_alpha: whether this function needs an alpha parameter. Default false.
#
#   needs_results: a list of MetaRequirement objects (below).
#                  Note that it is legal for meta estimators to depend on other
#                  meta estimators; circular dependencies cause the spec parser
#                  to crash.
#
# Arguments:
#
#   alphas (if needs_alpha; array-like, scalar or 1d): the alpha values to use
#
#   Ks (array-like, scalar or 1d): the K values used
#
#   dim (scalar): the dimension of the feature space
#
#   rhos: a list of within-bag NN distances, each of which is like the rhos
#         argument above
#
#   required: a list of the results array for each MetaRequirement classes,
#             each of shape (n_bags, n_bags, num_Ks).
#
# Returns: array of results.
# If needs_alpha, has shape (n_bags, n_bags, num_alphas, num_Ks);
# otherwise, has shape (n_bags, n_bags, num_Ks).

MetaRequirement = namedtuple('MetaRequirement', 'func alpha needs_transpose')
# func: the function of the regular divergence that's needed
# alpha: None if no alpha is needed. Otherwise, can be a scalar alpha value,
#        or a callable which takes the (scalar or list) alphas for the meta
#        function and returns the required function's alpha(s).
# needs_transpose: if true, ensure the required results also have a result for
#                  [j, i] for any [i, j] that we need


def bhattacharyya(Ks, dim, rhos, required, clamp=True):
    r'''
    Estimate the Bhattacharyya coefficient between distributions, based on kNN
    distances:  \int \sqrt{p q}

    If clamp (the default), enforces 0 <= BC <= 1.

    Returns an array of shape (num_Ks,).
    '''
    est, = required
    if clamp:
        est = np.minimum(est, 1)  # BC <= 1
    return est
bhattacharyya.needs_alpha = False
bhattacharyya.needs_results = [MetaRequirement(alpha_div, 0.5, False)]


def hellinger(Ks, dim, rhos, required):
    r'''
    Estimate the Hellinger distance between distributions, based on kNN
    distances:  \sqrt{1 - \int \sqrt{p q}}

    Always clamps 0 <= H <= 1.

    Returns a vector: one element for each K.
    '''
    bc, = required
    est = 1 - bc
    np.maximum(est, 0, out=est)
    np.sqrt(est, out=est)
    return est
hellinger.needs_alpha = False
hellinger.needs_results = [MetaRequirement(alpha_div, 0.5, False)]


def renyi(alphas, Ks, dim, rhos, required, min_val=eps, clamp=True):
    r'''
    Estimate the Renyi-alpha divergence between distributions, based on kNN
    distances:  1/(\alpha-1) \log \int p^alpha q^(1-\alpha)

    If the inner integral is less than min_val (default `utils.eps`), uses the
    log of min_val instead.

    If clamp (the default), enforces that the estimates are nonnegative by
    replacing any negative estimates with 0.

    Returns an array of shape (num_alphas, num_Ks).
    '''
    alphas = np.reshape(alphas, (-1, 1))
    est = np.concatenate(required, axis=2)

    # TODO: make sure modifying est doesn't modify the original data
    np.maximum(est, min_val, out=est)
    np.log(est, out=est)
    est /= alphas - 1
    if clamp:
        np.maximum(est, 0, out=est)
    return est
renyi.needs_alpha = True
renyi.needs_results = [MetaRequirement(alpha_div, identity, False)]


def tsallis(alphas, Ks, dim, rhos, required, clamp=True):
    r'''
    Estimate the Tsallis-alpha divergence between distributions, based on kNN
    distances:  (\int p^alpha q^(1-\alpha) - 1) / (\alpha - 1)

    If clamp (the default), enforces that the inner integral is nonnegative.

    Returns an array of shape (num_alphas, num_Ks).
    '''
    alphas = np.reshape(alphas, (-1, 1))
    alpha_est = required

    est = alpha_est - 1
    est /= alphas - 1
    # TODO: Tsallis is also nonnegative, no? Should we clamp it here?
    return est
tsallis.needs_alpha = True
tsallis.needs_results = [MetaRequirement(alpha_div, identity, False)]


def l2(Ks, dim, rhos, required):
    r'''
    Estimates the L2 distance between distributions, via
        \int (p - q)^2 = \int p^2 - \int p q - \int q p + \int q^2.

    \int pq and \int qp are estimated with the linear function (in both
    directions), while \int p^2 and \int q^2 are estimated via the quadratic
    function below.
    '''
    n_bags = len(rhos)

    linears, = required
    assert linears.shape == (n_bags, n_bags, 1, Ks.size)

    quadratics = np.empty((n_bags, Ks.size), dtype=np.float32)
    for i, rho in enumerate(rhos):
        quadratics[i, :] = quadratic(Ks, dim, rho)

    est = -linears
    est -= linears.transpose(1, 0, 2, 3)
    est += quadratics.reshape(n_bags, 1, 1, Ks.size)
    est += quadratics.reshape(1, n_bags, 1, Ks.size)
    np.maximum(est, 0, out=est)
    np.sqrt(est, out=est)

    # diagonal is of course known to be zero
    all_bags = lazy_range(n_bags)
    est[all_bags, all_bags, :, :] = 0
    return est
l2.needs_alpha = False
l2.needs_results = [MetaRequirement(linear, alpha=None, needs_transpose=True)]


# Not actually a meta-estimator, though it could be if it just repeated the
# values across rows (or columns).
def quadratic(Ks, dim, rhos, required=None):
    r'''
    Estimates \int p^2 based on kNN distances.

    In here because it's used in the l2 distance, above.

    Returns array of shape (num_Ks,).
    '''
    # Estimated with alpha=1, beta=0:
    #   B_{k,d,1,0} is the same as B_{k,d,0,1} in linear()
    # and the full estimator is
    #   B / (n - 1) * mean(rho ^ -dim)
    N = rhos.shape[0]
    Ks = np.asarray(Ks)
    Bs = (Ks - 1) / np.pi ** (dim / 2) * gamma(dim / 2 + 1)  # shape (num_Ks,)
    return Bs / (N - 1) * np.mean(rhos ** (-dim), axis=0)


def jensen_shannon(Ks, dim, rhos, required, clamp=False):
    r'''
    Estimate the difference between the Shannon entropy of an equally-weighted
    mixture between X and Y and the mixture of the Shannon entropies:

        JS(X, Y) = H[ (X + Y) / 2 ] - (H[X] + H[Y]) / 2

    We use a special case of the Hino-Murata weighted information estimator with
    a fixed M = n \alpha, about equivalent to the K-nearest-neighbor approach
    used for the other estimators:

        Hideitsu Hino and Noboru Murata (2013).
        Information estimators for weighted observations. Neural Networks.
        http://linkinghub.elsevier.com/retrieve/pii/S0893608013001676


    The estimator for JS(X, Y) is:

        log volume of the unit ball - log M + log(n + m - 1) + digamma(M)
        + 1/2 mean_X( d * log distance to the M/(n+m-1) quantile of X_i in X+Y
                                where X points have weight 1 / (2 n - 1)
                                  and Y points have weight n / (m (2 n - 1))
                      - digamma(# of neighbors in that ball) )
        + 1/2 mean_Y( d * log distance to the M/(n+m-1) quantile of Y_i in X+Y
                                where X points have weight m / (n (2 m - 1))
                                  and Y points have weight 1 / (2 m - 1)
                      - digamma(# of neighbors in that ball) )

        - 1/2 (log volume of the unit ball - log M + log(n - 1) + digamma(M))
        - 1/2 mean_X( d * log distance to the M/(n-1) quantile of X_i in X
                                where X points have weight 1 / (n - 1))
                      - digamma(# of neighbors in that ball) )

        - 1/2 (log volume of the unit ball - log M + log(m - 1) + digamma(M))
        - 1/2 mean_Y( d * log distance to the M/(n-1) quantile of Y_i in Y
                                where X points have weight 1 / (m - 1))
                      - digamma(# of neighbors in that ball) )

        =

        log(n + m - 1) + digamma(M)
        + 1/2 mean_X( d * log distance to the M/(n+m-1) quantile of X_i in X+Y
                                where X points have weight 1 / (2 n - 1)
                                  and Y points have weight n / (m (2 n - 1))
                      - digamma(# of neighbors in that ball) )
        + 1/2 mean_Y( d * log distance to the M/(n+m-1) quantile of Y_i in X+Y
                                where X points have weight m / (n (2 m - 1))
                                  and Y points have weight 1 / (2 m - 1)
                      - digamma(# of neighbors in that ball) )
        - 1/2 [log(n-1) + mean_X( d * log rho_M(X_i) )]
        - 1/2 [log(m-1) + mean_Y( d * log rho_M(Y_i) )]

    where the alpha-quantile of a point in a weighted set is the highest k
    such that w_(j) <= alpha, where w_(j) is the weight of the (j)th nearest
    neighbor (not including the point itself).
    '''
    ns = np.array([rho.shape[0] for rho in rhos])
    n_bags = ns.size
    cores, = required
    assert cores.shape == (n_bags, n_bags, 1, Ks.size)

    bits = np.empty((n_bags, Ks.size), dtype=np.float32)
    for i, rho in enumerate(rhos):  # TODO parallelize?
        bits[i, :] = dim * np.mean(np.log(rho), axis=0)
    bits += np.log(ns - 1)[:, np.newaxis]

    est = cores + cores.transpose(1, 0, 2, 3)  # intentionally make a copy
    est -= bits.reshape(n_bags, 1, 1, Ks.size)
    est -= bits.reshape(1, n_bags, 1, Ks.size)
    est /= 2
    est += np.log(-1 + ns[:, np.newaxis] + ns[np.newaxis, :])[:, :, None, None]
    est += psi(Ks)[None, None, None, :]

    # diagonal is zero
    all_bags = lazy_range(n_bags)
    est[all_bags, all_bags, :, :] = 0

    if clamp:  # know that 0 <= JS <= ln(2)
        np.maximum(0, est, out=est)
        np.minimum(np.log(2), est, out=est)
    return est
jensen_shannon.needs_alpha = False
jensen_shannon.needs_results = [
    MetaRequirement(jensen_shannon_core, alpha=None, needs_transpose=True)]


def js_clamp(Ks, dim, rhos, required):
    # TODO: less hacky solution to this problem
    js, = required
    est = np.maximum(0, js)
    np.minimum(np.log(2), est, out=est)
    return est
js_clamp.needs_alpha = False
js_clamp.needs_results = [
    MetaRequirement(jensen_shannon, alpha=None, needs_transpose=False)]



################################################################################

func_mapping = {
    'linear': linear,
    'kl': kl,
    'alpha': alpha_div,
    'bc': bhattacharyya,
    'hellinger': hellinger,
    'renyi': renyi,
    'tsallis': tsallis,
    'l2': l2,
    'js-core': jensen_shannon_core,
    'js': jensen_shannon,
    'jensen-shannon': jensen_shannon,
    'js_clamp': js_clamp,
}


def topological_sort(deps):
    '''
    Topologically sort a DAG, represented by a dict of child => set of parents.
    The dependency dict is destroyed during operation.

    Uses the Kahn algorithm: http://en.wikipedia.org/wiki/Topological_sorting
    Not a particularly good implementation, but we're just running it on tiny
    graphs.
    '''

    order = []
    available = set()

    def _move_available():
        to_delete = []
        for n, parents in iteritems(deps):
            if not parents:
                available.add(n)
                to_delete.append(n)
        for n in to_delete:
            del deps[n]

    _move_available()
    while available:
        n = available.pop()
        order.append(n)
        for parents in itervalues(deps):
            parents.discard(n)
        _move_available()

    if available:
        raise ValueError("dependency cycle found")
    return order


_FuncInfo = namedtuple('_FuncInfo', 'alphas pos')
_MetaFuncInfo = namedtuple('_MetaFuncInfo', 'alphas pos deps')
def _parse_specs(specs, Ks, dim, ns):
    '''
    Set up the different functions we need to call.

    Returns:
        - a dict mapping base estimator functions to _FuncInfo objects.
          If the function needs_alpha, then the alphas attribute is an array
          of alpha values and pos is a corresponding array of indices.
          Otherwise, alphas is None and pos is a list containing a single index.
          Indices are >= 0 if they correspond to something in a spec,
          and negative if they're just used for a meta estimator but not
          directly requested.
        - an OrderedDict mapping functions to _MetaFuncInfo objects.
          alphas and pos are like for _FuncInfo; deps is a list of indices
          which should be passed to the estimator. Note that these might be
          other meta functions; this list is guaranteed to be in an order
          such that all dependencies are resolved before calling that function.
          If no such order is possible, raise ValueError.
        - the number of meta-only results

    # TODO: update doctests for _parse_specs

    >>> _parse_specs(['renyi:.8', 'hellinger', 'renyi:.9'])
    ({<function alpha_div at 0x10954f848>:
            _FuncInfo(alphas=[0.8, 0.5, 0.9], pos=[-1, -2, -3])},
     OrderedDict([
        (<function hellinger at 0x10954fc80>,
            _MetaFuncInfo(alphas=None, pos=[1], deps=[array(-2)])),
        (<function renyi at 0x10954fcf8>,
            _MetaFuncInfo(alphas=[0.8, 0.9], pos=[0, 2], deps=[-1, -3]))
     ]), 3)

    >>> _parse_specs(['renyi:.8', 'hellinger', 'renyi:.9', 'l2'])
    ({<function alpha_div at 0x10954f848>:
        _FuncInfo(alphas=[0.8, 0.5, 0.9], pos=[-1, -2, -3]),
      <function linear at 0x10954f758>: _FuncInfo(alphas=None, pos=[-4])
     }, OrderedDict([
        (<function hellinger at 0x10954fc80>,
            _MetaFuncInfo(alphas=None, pos=[1], deps=[array(-2)])),
        (<function l2 at 0x10954fde8>,
            _MetaFuncInfo(alphas=None, pos=[3], deps=[-4])),
        (<function renyi at 0x10954fcf8>,
            _MetaFuncInfo(alphas=[0.8, 0.9], pos=[0, 2], deps=[-1, -3]))
     ]), 4)

    >>> _parse_specs(['renyi:.8', 'hellinger', 'renyi:.9', 'l2', 'linear'])
    ({<function alpha_div at 0x10954f848>:
        _FuncInfo(alphas=[0.8, 0.5, 0.9], pos=[-1, -2, -3]),
      <function linear at 0x10954f758>: _FuncInfo(alphas=None, pos=[4])
     }, OrderedDict([
        (<function hellinger at 0x10954fc80>,
            _MetaFuncInfo(alphas=None, pos=[1], deps=[array(-2)])),
        (<function l2 at 0x10954fde8>,
            _MetaFuncInfo(alphas=None, pos=[3], deps=[4])),
        (<function renyi at 0x10954fcf8>,
            _MetaFuncInfo(alphas=[0.8, 0.9], pos=[0, 2], deps=[-1, -3]))
     ]), 3)
    '''
    funcs = {}
    metas = {}
    meta_deps = defaultdict(set)

    def add_func(func, alpha=None, pos=None):
        needs_alpha = getattr(func, 'needs_alpha', False)
        is_meta = hasattr(func, 'needs_results')

        d = metas if is_meta else funcs
        if func not in d:
            if needs_alpha:
                args = {'alphas': [alpha], 'pos': [pos]}
            else:
                args = {'alphas': None, 'pos': [pos]}

            if not is_meta:
                d[func] = _FuncInfo(**args)
            else:
                d[func] = _MetaFuncInfo(deps=[], **args)
                for req in func.needs_results:
                    if callable(req.alpha):
                        req_alpha = req.alpha(alpha)
                    else:
                        req_alpha = req.alpha
                    add_func(req.func, alpha=req_alpha)
                    meta_deps[func].add(req.func)
                    meta_deps[req.func]  # make sure required func is in there

        else:
            # already have an entry for the func
            # need to give it this pos, if it's not None
            # and also make sure that the alpha is present
            info = d[func]
            if not needs_alpha:
                if pos is not None:
                    if info.pos != [None]:
                        msg = "{} passed more than once"
                        raise ValueError(msg.format(func_name))

                    info.pos[0] = pos
            else:  # needs alpha
                try:
                    idx = info.alphas.index(alpha)
                except ValueError:
                    # this is a new alpha value we haven't seen yet
                    info.alphas.append(alpha)
                    info.pos.append(pos)
                    if is_meta:
                        for req in func.needs_results:
                            if callable(req.alpha):
                                req_alpha = req.alpha(alpha)
                            else:
                                req_alpha = req.alpha
                            add_func(req.func, alpha=req_alpha)
                else:
                    # repeated alpha value
                    if pos is not None:
                        if info.pos[idx] is not None:
                            msg = "{} with alpha {} passed more than once"
                            raise ValueError(msg.format(func_name, alpha))
                        info.pos[idx] = pos

    # add functions for each spec
    for i, spec in enumerate(specs):
        func_name, alpha = (spec.split(':', 1) + [None])[:2]
        if alpha is not None:
            alpha = float(alpha)

        try:
            func = func_mapping[func_name]
        except KeyError:
            msg = "'{}' is not a known function type"
            raise ValueError(msg.format(func_name))

        needs_alpha = getattr(func, 'needs_alpha', False)
        if needs_alpha and alpha is None:
            msg = "{} needs alpha but not passed in spec '{}'"
            raise ValueError(msg.format(func_name, spec))
        elif not needs_alpha and alpha is not None:
            msg = "{} doesn't need alpha but is passed in spec '{}'"
            raise ValueError(msg.format(func_name, spec))

        add_func(func, alpha, i)

    # number things that are dependencies only
    meta_counter = itertools.count(-1, step=-1)
    for info in itertools.chain(itervalues(funcs), itervalues(metas)):
        for i, pos in enumerate(info.pos):
            if pos is None:
                info.pos[i] = next(meta_counter)

    # fill in the dependencies for metas
    for func, info in iteritems(metas):
        deps = info.deps
        assert deps == []

        for req in func.needs_results:
            f = req.func
            req_info = (metas if hasattr(f, 'needs_results') else funcs)[f]
            if req.alpha is not None:
                if callable(req.alpha):
                    req_alpha = req.alpha(info.alphas)
                else:
                    req_alpha = req.alpha

                find_alpha = np.vectorize(req_info.alphas.index, otypes=[int])
                pos = np.asarray(req_info.pos)[find_alpha(req_alpha)]
                if np.isscalar(pos):
                    deps.append(pos[()])
                else:
                    deps.extend(pos)
            else:
                pos, = req_info.pos
                deps.append(pos)

    # topological sort of metas
    meta_order = topological_sort(meta_deps)
    metas_ordered = OrderedDict(
        (f, metas[f]) for f in meta_order if hasattr(f, 'needs_results'))

    # replace functions with partials of args
    def replace_func(func, info):
        needs_alpha = getattr(func, 'needs_alpha', False)

        new = None
        args = (Ks, dim)
        if needs_alpha:
            args = (info.alphas,) + args

        if hasattr(func, 'chooser_fn'):
            args += (ns,)
            if (getattr(func, 'needs_all_ks', False) and
                    getattr(func.chooser_fn, 'returns_ks', False)):
                new, k = func.chooser_fn(*args)
                new.k_needed = k
            else:
                new = func.chooser_fn(*args)
        else:
            new = partial(func, *args)

        for attr in dir(func):
            if not (attr.startswith('__') or attr.startswith('func_')):
                setattr(new, attr, getattr(func, attr))
        return new

    rep_funcs = dict(
        (replace_func(f, info), info) for f, info in iteritems(funcs))
    rep_metas_ordered = OrderedDict(
        (replace_func(f, info), info) for f, info in iteritems(metas_ordered))

    return rep_funcs, rep_metas_ordered, -next(meta_counter) - 1


def normalize_div_name(name):
    if ':' in name:
        main, alpha = name.split(':')
        return '{}:{}'.format(main, float(alpha))
    return name


################################################################################
### The main dealio

class _DivEstimator(object):
    def __init__(self, features, mask=None, specs=['kl'], Ks=[3],
                 cores=None, algorithm=None, min_dist=None,
                 status_fn=True, progressbar=None, **flann_args):
        if progressbar is None:
            progressbar = status_fn is True
        self.status_fn = status_fn = get_status_fn(status_fn)
        self.progressbar = progressbar

        if not isinstance(features, Features):
            raise TypeError("features should be a Features instance")
        n_bags = len(features)
        dim = features.dim
        self.features = features

        if mask is None:
            mask = np.ones((n_bags, n_bags), dtype=bool)
        else:
            mask = np.asarray(mask)
            if mask.shape != (n_bags, n_bags):
                msg = "mask should be n x n, not {}"
                raise TypeError(msg.format(mask.shape))
            elif mask.dtype.kind != 'b':
                msg = "mask should be a boolean array, not {}"
                raise TypeError(msg.format(mask.dtype))
        self.mask = mask

        self.Ks = Ks = np.array(np.squeeze(Ks), ndmin=1, dtype=np.int32)
        if Ks.ndim != 1:
            msg = "Ks should be 1-dim, got shape {}"
            raise TypeError(msg.format(Ks.shape))
        if Ks.min() < 1:
            raise ValueError("Ks should be positive; got {}".format(Ks.min()))
        if Ks.max() >= features._n_pts.min():
            msg = "asked for K = {}, but there's a bag with only {} points"
            raise ValueError(msg.format(Ks.max(), features._n_pts.min()))
        self.max_K = Ks.max()

        self.funcs, self.metas, self.n_meta_only = \
                _parse_specs(specs, Ks, dim, features._n_pts)
        self.specs = specs

        self.save_all_Ks = False
        for func in self.funcs:
            if hasattr(func, 'k_needed'):
                self.max_K = max(self.max_K, func.k_needed)
                self.save_all_Ks = True
                # TODO: could be more efficient about this
                # eg if we need [1, 2, ..., 5] and 20, no need to save 6 to 19
                # (but that won't happen with the current estimators)

        if cores is None:
            from multiprocessing import cpu_count
            cores = cpu_count()
        flann_args['cores'] = cores

        if algorithm is None:
            algorithm = pick_flann_algorithm(dim)
        flann_args['algorithm'] = algorithm

        try:
            FLANNParameters(**flann_args)
        except AttributeError as e:
            msg = "_DivEstimator got an unexpected keyword argument:\n  {}"
            raise TypeError(msg.format(e))
        self.flann_args = flann_args

        if min_dist is None:
            min_dist = default_min_dist(dim)
        self.min_dist = min_dist

        status_fn('kNN processing: K = {} on {!r}'.format(self.max_K, features))

    def full_est(self):
        self.build_indices()
        self.get_rhos()
        self.get_cross_divs()
        self.finalize()
        return self.outputs

    def build_indices(self):
        self.status_fn('Building indices...')
        # Build indices for each bag. Do this one-at-a-time for now.
        # TODO: should probably multithread this
        def _make_index(bag):
            idx = FLANNIndex(**self.flann_args)
            idx.build_index(bag)
            return idx

        pbar = progress() if self.progressbar else identity
        self.indices = [_make_index(b) for b in pbar(self.features.features)]
        if self.progressbar:
            pbar.finish()

    def get_rhos(self):
        self.status_fn('\nGetting within-bag distances...')
        # need to throw away the closet neighbor, which will always be self
        # this means that K=1 corresponds to column 1 in the array
        which_Ks = slice(1, None) if self.save_all_Ks else self.Ks
        max_K = self.max_K
        min_dist = self.min_dist
        maximum = np.maximum
        pbar = progress() if self.progressbar else identity

        self.rhos = [
            maximum(min_dist,
                    np.sqrt(idx.nn_index(bag, max_K + 1)[1][:, which_Ks]))
            for bag, idx in izip(self.features.features, pbar(self.indices))]
        if self.progressbar:
            pbar.finish()

    def get_cross_divs(self):
        self.status_fn('\nGetting cross-bag distances and divergences...')
        # If anything needs its transpose also, then we just compute everything
        # with the transpose; we'll nan out the unnecessary bits later.
        # TODO: only compute the things we need transposed...
        mask = self.mask
        self.should_mask = False
        if any(req.needs_transpose for f in self.metas
                                   for req in f.needs_results):
            if np.any(mask != mask.T):
                mask = mask + mask.T
                self.should_mask = True

        self.outputs = _estimate_cross_divs(
            self.features, self.indices, self.rhos,
            mask.view(np.uint8), self.funcs,
            self.Ks, self.max_K, self.save_all_Ks,
            self.specs, self.n_meta_only,
            self.progressbar, self.flann_args['cores'], self.min_dist)

    def finalize(self):
        if self.save_all_Ks:
            rhos = [rho[:, self.Ks - 1] for rho in self.rhos]
        else:
            rhos = self.rhos
        for meta, info in iteritems(self.metas):
            required = [self.outputs[:, :, [i], :] for i in info.deps]
            r = meta(rhos, required)
            if r.ndim == 3:
                r = r[:, :, np.newaxis, :]
            self.outputs[:, :, info.pos, :] = r

        if self.n_meta_only:
            self.outputs = np.ascontiguousarray(
                self.outputs[:, :, :-self.n_meta_only, :])

        if self.should_mask:
            self.outputs[~self.mask] = np.nan


def estimate_divs(features,
                  mask=None,
                  specs=['kl'],
                  Ks=[3],
                  cores=None,
                  algorithm=None,
                  min_dist=None,
                  status_fn=True, progressbar=None,
                  return_opts=False,
                  **flann_args):
    '''
    Gets the divergences between bags.

    Parameters:
        features: a Features instance containing n bags of features.
        mask (optional): an n x n boolean array indicating whether to
                         estimate each div pair. Any not estimated are returned
                         as nan in the output. Default: estimate all.
        specs: a list of strings of divergence specs. TODO: document
        Ks: a list of K values to estimate the divergences with.
            Note that if you're estimating Jensen differences, we use the K
            values as the Hino-Murata "M" value, which if all the sets are the
            same size corresponds to the K-nearest-neighbor, but for different-
            sized sets may involve doing a KNN search for a higher value of K.
            (In the worst case with very differently-sized sets, it's doubled.)
        cores: number of threads to use for estimating in parallel. None uses
               all cores on the machine.
        algorithm: the FLANN algorithm to use. Defaults to kdtree_single when
                   dimensionality is 5 or less, linear otherwise. (These give
                   exact answers; approximate solutions may be significantly
                   faster but require tuning.)
        min_dist: a minimum distance to use in kNN searches. Defaults to the
                  return value of default_min_dist().
        status_fn: a function to print out status messages.
                   None means don't print any; True prints to stderr.
        progressbar: show a progress bar on stderr. Default: (status_fn is True)
        return_opts: return a dictionary of options used as the second value.
        other options: passed along to FLANN for nearest-neighbor searches

    Returns an array of shape (n, n, num_specs, num_Ks), whose (i, j, k, l)
    value is the estimate of D(features[i] || features[j]) with specs[k] using
    Ks[l].
    '''
    # TODO: document how progressbar works
    # TODO: other kinds of callbacks for showing progress bars
    est = _DivEstimator(features=features, mask=mask, specs=specs, Ks=Ks,
                        cores=cores, algorithm=algorithm, min_dist=min_dist,
                        status_fn=status_fn, progressbar=progressbar,
                        **flann_args)
    return est.full_est()


################################################################################
### Command line interface

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute divergences and set kernels based on "
                    "KNN statistics.")

    parser.add_argument('input_file',
        help="The input file, an HDF5 file (e.g. .mat with -v7.3).")
    parser.add_argument('--input-format',
        choices=['matlab', 'python'], default='python',
        help="Whether the features file was generated by the matlab code or "
             "the python code; default python.")
    parser.add_argument('--input-var-name', default='features',
        help="The name of the cell array of row-instance data matrices, "
             "if the input file is matlab format.")

    parser.add_argument('output_file', nargs='?',
        help="Name of the output file; default input_file.divs.(mat|h5).")
    parser.add_argument('--output-format',
        choices=['hdf5', 'mat'], default='hdf5',
        help="Output file format; default %(default)s.")

    parser.add_argument('--cores', '--n-proc', type=positive_int, default=None,
        help="Number of processes to use; default is as many as CPU cores.")

    parser.add_argument('--div-funcs', nargs='*',
        default=['hellinger', 'bc', 'linear', 'l2', 'kl',
                 'renyi:.5', 'renyi:.7', 'renyi:.9', 'renyi:.99'],
        help="The divergences to estimate. Default: %(default)s.")

    parser.add_argument('-K', nargs='*', type=positive_int,
        default=[1, 3, 5, 10],
        help="The numbers of nearest neighbors to calculate. "
             "Default: %(default)s.")

    parser.add_argument('--min-dist', type=float, default=None,
        help="Protect against identical points by making sure kNN distances "
             "are always at least this big. Default: the smaller of .01 and "
             "10 ^ (100 / dim).")

    # TODO: nice thing for FLANN nearest-neighbor algorithm selection
    import ast
    parser.add_argument('--flann-args', type=ast.literal_eval, default={},
        help="A dictionary of arguments to FLANN.")

    args = parser.parse_args()
    if args.output_file is None:
        args.output_file = '{}.divs.{}'.format(
            args.input_file, 'mat' if args.output_format == 'mat' else 'h5')

    return args


def main():
    import h5py

    args = parse_args()
    status_fn = get_status_fn(True)

    status_fn('Reading data...')
    if args.input_format == 'matlab':
        with h5py.File(args.input_file, 'r') as f:
            feats = read_cell_array(f, f[args.input_var_name])
            for x in ['cats', 'categories', 'labels']:
                if x in f:
                    cats = np.squeeze(f[x][()])
                    break
            else:
                cats = None
        bags = Features(feats, categories=cats)
    else:
        bags = Features.load(args.input_file)

    if args.min_dist is None:
        args.min_dist = default_min_dist(bags.dim)

    if args.output_format == 'mat':
        confirm_outfile(args.output_file)
    else:
        if not os.path.exists(args.output_file):
            confirm_outfile(args.output_file)
        else:
            check_h5_file_agreement(args.output_file, features=bags, args=args)
            status_fn("Output file already exists, but agrees with args.")

    Ks = np.asarray(args.K)
    if args.min_dist is None:
        args.min_dist = default_min_dist(args.min_dist)

    divs = estimate_divs(
            bags, specs=args.div_funcs, Ks=Ks,
            cores=args.cores,
            min_dist=args.min_dist,
            status_fn=True,
            progressbar=True,
            return_opts=True,
            **args.flann_args)

    status_fn("Outputting results to", args.output_file)

    opts = {
        'specs': args.div_funcs,
        'Ks': args.K,
        'min_dist': args.min_dist,
        'dim': bags.dim,
        'cats': bags.categories,
        'names': bags.names,
        'Ds': divs,
    }

    if args.output_format == 'mat':
        scipy.io.savemat(args.output_file, opts, oned_as='column')
    else:
        add_to_h5_file(args.output_file, opts)

    if np.any(np.isnan(divs)):
        warnings.warn('nan divergence calculated')
    if np.any(np.isinf(divs)):
        warnings.warn('infinite divergence calculated')


################################################################################
### Stuff relating to result files

def _convert_cats(ary):
    ary = np.asarray(ary)

    kind = ary.dtype.kind
    if kind == 'O':
        assert isinstance(ary[0], str_types)
        is_str = True
    elif kind in 'SUa':
        is_str = True
    elif kind in 'fc':
        is_str = False
        as_int = ary.astype(int)
        assert np.all(ary == as_int)
        ary = as_int
    elif kind in 'iub':
        is_str = False
    else:
        raise TypeError

    if is_str:
        import h5py
        ary = np.asarray(ary, h5py.special_dtype(vlen=bytes))
    return ary, is_str


def reconcile_file_order(f, names=None, cats=None, write=False):
    '''
    Checks that the passed names, cats agree with the cache file f. If both have
    names, checks only that; otherwise, checks that they agree as well as
    possible.

    f: an h5py.File
    names: a string array or None
    cats: a string array, an array of integers, or None
    write: if true, add any additional info to the file once they seem the same
    '''
    # TODO: remove support for integer categories

    have_names = names is not None
    have_cats = cats is not None

    if not have_names and not have_cats:
        raise ValueError("reconcile_file_order needs names or cats...")

    if '_meta' in f:
        meta_group = f['_meta']

        have_f_names = 'names' in meta_group
        have_f_cats = 'cats' in meta_group
    else:
        meta_group = None
        have_f_names = have_f_cats = False

    if have_names:
        import h5py
        names = np.asarray(names, dtype=h5py.special_dtype(vlen=bytes))
    if have_f_names:
        f_names = meta_group['names'][()]

    if have_cats:
        cats, cats_is_str = _convert_cats(cats)
    if have_f_cats:
        f_cats, f_cats_is_str = _convert_cats(meta_group['cats'][()])

    # check name agreement, if both sides have it
    if have_names and have_f_names:
        assert np.all(names == f_names)

    # check category agreement
    if have_cats and have_f_cats:
        if cats_is_str and f_cats_is_str:
            assert np.all(cats == f_cats)
        else:
            # at least one, maybe both, are just ints
            # so we only want to check equivalence up to relabelings
            _, cats_relabeled = np.unique(cats, return_inverse=True)
            _, f_cats_relabeled = np.unique(f_cats, return_inverse=True)
            assert np.all(cats_relabeled == f_cats_relabeled)

    # Everything agrees to as much as we can check it.
    # Now it's time to write anything we have that the file doesn't.
    if write:
        if meta_group is None:
            meta_group = f.create_group('meta')
        if have_names and not have_f_names:
            meta_group['names'] = names
        if (have_cats and
                (not have_f_cats or (cats_is_str and not f_cats_is_str))):
            meta_group['cats'] = cats


# TODO: track flann algorithms used here? or just whether they're exact?
def check_h5_settings(f, n, dim, min_dist=None,
                      names=None, cats=None, write=False):
    """
    Checks that the hdf5 div cache file has settings that agree with the
    passed settings. If write, adds them to the file if not present.
    """
    if any(divs.shape != (n, n)
           for name, div_group in f.items() if name != '_meta'
           for divs in div_group.values()):
        raise ValueError("existing divs have wrong shape")

    if '_meta' in f:
        meta_group = f['_meta']
        def check(name, value):
            if np.any(meta_group[name][()] != value):
                raise ValueError("attribute '{}' differs in file".format(name))
    elif write:
        meta_group = f.require_group('_meta')
        def check(name, value):
            meta_group[name] = value
    else:
        meta_group = None
        def check(name, value):
            pass

    check('dim', dim)
    check('min_dist', default_min_dist(dim) if min_dist is None else min_dist)

    for x in ['names', 'cats']:
        if meta_group is not None and x in meta_group:
            if meta_group[x].shape != (n,):
                raise ValueError("'{}'' has wrong shape in file".format(x))
    if names is not None or cats is not None:
        reconcile_file_order(f, names=names, cats=cats, write=write)


def add_to_h5_cache(f, div_dict, dim, min_dist, names=None, cats=None):
    """
    Add some divergences to an hdf5 file of divergences.
    Overwrites any matching ones that already exist.

        f: an h5py.File object
        div_dict: dict of (div_func, K) => divs array
    """
    # check shapes all agree for div_dict
    m, n = next(iter(itervalues(div_dict))).shape
    assert m == n
    del m
    assert all(div.shape == (n, n) for div in itervalues(div_dict))

    check_h5_settings(f, n=n,
                      dim=dim, min_dist=min_dist,
                      names=names, cats=cats, write=True)

    for (div_func, K), divs in iteritems(div_dict):
        g = f.require_group(normalize_div_name(div_func))
        name = str(K)
        if name in g:
            del g[name]
        g.create_dataset(name, data=divs)


def add_to_h5_file(filename, data):
    import h5py
    with h5py.File(filename) as f:
        div_dict = dict(
            ((name, K), data['Ds'][:, :, i, j])
            for i, name in enumerate(data['specs'])
            for j, K in enumerate(data['Ks'])
        )

        add_to_h5_cache(f, div_dict,
                        dim=data['dim'], min_dist=data['min_dist'],
                        names=data.get('names', None),
                        cats=data.get('cats', None))


def check_h5_file_agreement(filename, features, args, interactive=True):
    import h5py
    with h5py.File(filename) as f:
        # output file already exists; make sure args agree
        if not f.keys():
            return

        check_h5_settings(f, n=len(features),
                          dim=features.dim, min_dist=args.min_dist,
                          names=features.names, cats=features.categories,
                          write=False)

        # any overlap with stuff we've already calculated?
        div_funcs = strict_map(normalize_div_name, args.div_funcs)
        overlap = [(div_func, k)
                   for div_func in div_funcs if div_func in f
                   for k in args.K if str(k) in f[div_func]]
        if overlap:
            if not interactive:
                raise ValueError("hdf5 conflict: {}".format(overlap))

            msg = '\n'.join(
                ["WARNING: the following divs will be overwritten:"] +
                ['\t{:12} k = {}'.format(df, ', '.join(str(k) for d, k in d_ks))
                 for df, d_ks in itertools.groupby(overlap, itemgetter(0))] +
                ['Proceed? [yN] '])
            resp = raw_input(msg)
            if not resp.startswith('y'):
                sys.exit("Aborting.")


################################################################################
if __name__ == '__main__':
    main()
