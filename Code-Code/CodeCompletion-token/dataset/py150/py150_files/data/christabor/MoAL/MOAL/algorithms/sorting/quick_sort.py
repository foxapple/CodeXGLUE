# -*- coding: utf-8 -*-

__author__ = """Chris Tabor (dxdstudio@gmail.com)"""

if __name__ == '__main__':
    from os import getcwd
    from os import sys
    sys.path.append(getcwd())

from MOAL.helpers.display import Section
from MOAL.helpers.generic import swap_item
from MOAL.helpers.trials import run_sorting_trials
from pprint import pprint as ppr


# Based off algorithm from http://en.wikipedia.org/wiki/Quicksort

def quick_sort(items, low=None, high=None):

    def partition(items, low, high):
        pivot_index = (low + high) / 2
        pivot_value = items[pivot_index]
        items = swap_item(items, pivot_index, high)
        store_index = low
        for k in range(low, high):
            if items[k] < pivot_value:
                items = swap_item(items, k, store_index)
                store_index += 1
        items = swap_item(items, store_index, high)
        return store_index

    num_items = len(items)
    if len(items) < 2:
        return items
    if low is None:
        low = 0
    if high is None:
        high = num_items - 1
    if low < high:
        partitioned = partition(items, low, high)
        quick_sort(items, low=low, high=partitioned - 1)
        quick_sort(items, low=partitioned + 1, high=high)
    return items


if __name__ == '__main__':
    with Section('Quick Sort'):
        ppr(run_sorting_trials(quick_sort, magnitudes=[10, 100, 1000]))
