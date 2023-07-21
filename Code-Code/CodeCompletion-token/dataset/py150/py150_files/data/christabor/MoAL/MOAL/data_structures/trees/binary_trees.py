# -*- coding: utf-8 -*-

__author__ = """Chris Tabor (dxdstudio@gmail.com)"""

if __name__ == '__main__':
    from os import getcwd
    from os import sys
    sys.path.append(getcwd())

from MOAL.helpers.display import Section
from MOAL.helpers.display import print_h4
from MOAL.helpers.display import cmd_title
from MOAL.data_structures.abstract.tree import Tree

DEBUG = True if __name__ == '__main__' else False


class InvalidChildNodeCount(Exception):
    pass


class BinaryTree(Tree):
    """A binary tree is the same as a tree ADT, except each node must have a max
    of two child nodes, unless it's a leaf node, in which case it has zero."""

    def __setitem__(self, key, val):
        if len(val['edges']) > 2:
            raise InvalidChildNodeCount(
                'Binary Tree cannot have more than two children!')
        super(BinaryTree, self).__setitem__(key, val)

    def get_left_child(self, node):
        if len(node['edges']) == 0:
            return None
        return node['edges'][0]

    def get_right_child(self, node):
        if len(node['edges']) < 2:
            return None
        return node['edges'][1]

    def is_degenerate(self):
        # TODO
        pass

    def is_pathological(self):
        # TODO
        return self.is_degenerate()


class NaiveBinarySearchTree(BinaryTree):

    def __init__(self, *args, **kwargs):
        super(NaiveBinarySearchTree, self).__init__(*args, **kwargs)
        self.rebalance_children(self.get_root()['node'])

    def __setitem__(self, key, val):
        super(NaiveBinarySearchTree, self).__setitem__(key, val)
        self.rebalance_children(key)

    def _lt(self, node_a, node_b):
        """Comparator function, which can be used to implement a BST.
        This should be sub-classed and overridden for custom comparisons,
        beyond typical integer comparison of BSTs."""
        node_a = self.__getitem__(node_a)
        node_b = self.__getitem__(node_b)
        if 'val' in node_a and 'val' in node_b:
            return node_a['val'] > node_b['val']
        else:
            return False

    def rebalance_children(self, node, current=None):
        """Does a cascade of re-balances, but only for each child node.
        The first index is the left, and the second, the right, so
        re-balancing these child nodes is simply ensuring largest comes last."""
        print('Balancing children...')
        if current is not None:
            node = self.__getitem__(current)
            node['edges'] = sorted(node['edges'])
            self.rebalance_children(node, current=node)
        else:
            node = self.__getitem__(node)
            node['edges'] = sorted(node['edges'])


class BifurcatingArborescence(BinaryTree):
    """A hilariously verbose alternative name for a Binary Tree!"""


if DEBUG:
    with Section('Binary Tree'):
        """
                            0  root
                           / \
                          /   \
                         1     2  interior
                        /     / \
                       /     /   \
                      3     4     5  leaves

          The tree above is represented in python code below.

        """
        data = {
            0: {'edges': [1, 2], 'is_root': True},
            1: {'edges': [3], 'parent': 0},
            2: {'edges': [4, 5], 'parent': 0},
            3: {'edges': [], 'parent': 1},
            4: {'edges': [], 'parent': 2},
            5: {'edges': [], 'parent': 2},
        }
        btree = BinaryTree(data)
        print(btree)

        print_h4(
            'Binary trees',
            desc=('They can have no more than two nodes, '
                  'so adding new edges that do not conform'
                  ' should throw an error.'))
        try:
            btree[6] = {'edges': [7, 8, 9], 'parent': 3}
        except InvalidChildNodeCount:
            cmd_title('Error called successfully', newlines=False)

        bst = NaiveBinarySearchTree(data)
        print(bst)

        bst.add_child(5, 6)
        bst.add_siblings(5, [10, 11])
        print(bst)
