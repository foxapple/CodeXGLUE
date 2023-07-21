#! /usr/bin/env python

import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from os import path
from random import Random, randint

import coverage

class RandomOrderTestSuite(unittest.TestSuite):
    """
    Test Suite that will randomize the order of tests.  This avoids the tests
    becoming dependent on some overlooked state.  USE WITH CAUTION.
    """

    def __init__(self, seed, *args, **kwargs):
        if seed:
            self.__seed = seed
        else:
            self.__seed = randint(0, 9999)
        super(RandomOrderTestSuite, self).__init__(*args, **kwargs)

    def __get_all_tests(self, test_case):
        result = []
        for item in test_case:
            if hasattr(item, "_tests") and len(item._tests) > 0:
                result += self.__get_all_tests(item)
            else:
                result.append(item)
        return result

    def run(self, result):
        cases = self.__get_all_tests(self)
        r = Random(self.__seed)
        r.shuffle(cases)
        for test in cases:
            if result.shouldStop:
                break
            test(result)
        print
        print
        print '>>> python runtests.py --seed={0}'.format(self.__seed)
        return result

if __name__ == "__main__":
    cov = coverage.coverage(source=[path.join(path.dirname(__file__), 'datatree')])
    cov.start()

    seed = None
    for arg in sys.argv:
        if arg.startswith('--seed='):
            seed = int(arg.split('=')[1])

    current_folder = path.dirname(__file__)
    base_folder = path.join(current_folder, "datatree")

    sys.path.insert(0, current_folder)

    suite = RandomOrderTestSuite(seed)
    loader = unittest.loader.defaultTestLoader
    suite.addTest(loader.discover(base_folder, pattern="test*.py"))
    runner = unittest.TextTestRunner()
    runner.verbosity = 2

    runner.run(suite.run)
    cov.stop()
    # Output the coverage
    cov.html_report(directory='htmlcov')
    print 'Coverage report written to: {0}'.format(path.join(path.dirname(__file__), 'htmlcov', 'index.html'))
