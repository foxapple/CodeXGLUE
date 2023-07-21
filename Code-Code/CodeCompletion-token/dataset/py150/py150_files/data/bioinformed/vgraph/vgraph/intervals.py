# -*- coding: utf-8 -*-

## Copyright 2015 Kevin B Jacobs
##
## Licensed under the Apache License, Version 2.0 (the "License"); you may
## not use this file except in compliance with the License.  You may obtain
## a copy of the License at
##
##        http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
## WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
## License for the specific language governing permissions and limitations
## under the License.


from heapq    import heappop, heapreplace, heapify
from operator import attrgetter


def augment_intervals(it, i, key):
    last = None
    for value in it:
        k = key(value)
        if last is not None and k < last:
            raise ValueError('invalid order')
        yield k, i, value


def iter_merge(iterators, key=id):
    augmented = [augment_intervals(it, i, key) for i, it in enumerate(iterators)]
    for min_key, index, value in merge(augmented):
        yield index, value


def merge(iterables):
    '''Merge multiple sorted inputs into a single sorted output.

    Similar to sorted(itertools.chain(*iterables)) but returns a generator,
    does not pull the data into memory all at once, and assumes that each of
    the input streams is already sorted (smallest to largest).
    '''
    _heappop, _heapreplace, _StopIteration = heappop, heapreplace, StopIteration

    h = []
    h_append = h.append
    for i, it in enumerate(map(iter, iterables)):
        try:
            next = it.next if hasattr(it, 'next') else it.__next__
            h_append([next(), i, next])
        except _StopIteration:
            pass

    heapify(h)

    while 1:
        try:
            while 1:
                v, i, next = s = h[0]       # raises IndexError when h is empty
                s[0] = next()               # raises StopIteration when exhausted
                yield v
                _heapreplace(h, s)          # restore heap condition
        except _StopIteration:
            _heappop(h)                     # remove empty iterator
            yield v
        except IndexError:
            return


def demultiplex_records(n, records):
    demux = [[] for _ in xrange(n)]
    for i, r in records:
        demux[i].append(r)
    return demux


def union(record_list, min_distance=0, interval_func=attrgetter('start', 'stop')):
    '''
    >>> from operator import itemgetter
    >>> ifunc = itemgetter(0,1)

    >>> l1 = [(0,1),(1,2),(2,3),(3,4),(4,5)]
    >>> l2 = [(1,2),(3,4)]
    >>> for start, stop, vals in union([l1,l2], 0, ifunc):
    ...     print start, stop, vals
    0 1 [[(0, 1)], []]
    1 2 [[(1, 2)], [(1, 2)]]
    2 3 [[(2, 3)], []]
    3 4 [[(3, 4)], [(3, 4)]]
    4 5 [[(4, 5)], []]

    >>> for start, stop, vals in union([l1,l2], 1, ifunc):
    ...     print start, stop, vals
    0 5 [[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)], [(1, 2), (3, 4)]]

    >>> l1 = [(0,5),(10,15),(20,25)]
    >>> l2 = [(5,11),(21,21)]
    >>> for start, stop, vals in union([l1,l2], 0, ifunc):
    ...     print start, stop, vals
    0 5 [[(0, 5)], []]
    5 15 [[(10, 15)], [(5, 11)]]
    20 25 [[(20, 25)], [(21, 21)]]

    >>> l1 = [(0,5),(10,15),(20,25)]
    >>> for start, stop, vals in union([l1, []], 0, ifunc):
    ...     print start, stop, vals
    0 5 [[(0, 5)], []]
    10 15 [[(10, 15)], []]
    20 25 [[(20, 25)], []]

    >>> for start, stop, vals in union([[], l1], 0, ifunc):
    ...     print start, stop, vals
    0 5 [[], [(0, 5)]]
    10 15 [[], [(10, 15)]]
    20 25 [[], [(20, 25)]]
    '''
    n = len(record_list)
    start = stop = 0
    records = []

    for i, rec in iter_merge(record_list, key=interval_func):
        rec_start, rec_stop = interval_func(rec)

        if not records or min_distance <= rec_start - stop:
            if records:
                yield start, stop, demultiplex_records(n, records)
                records = []
            start, stop = rec_start, rec_stop

        assert rec_start >= start
        records.append((i, rec))
        stop = max(stop, rec_stop)

    if records:
        yield start, stop, demultiplex_records(n, records)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
