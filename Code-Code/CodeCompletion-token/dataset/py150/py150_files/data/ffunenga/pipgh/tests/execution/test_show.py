import unittest

import pipgh


class TestShow(unittest.TestCase):

    def test_execution(self):
        argv = ['show', 'docopt/docopt']
        response, readme = pipgh.show(True, argv, output=False)
        self.assertGreaterEqual(response['full_name'], argv[1])

    def test_show_key(self):
        argv = ['show', '--clone-url', 'pypa/pip']
        val = pipgh.show(True, argv, output=False)
        self.assertTrue(val.endswith('github.com/pypa/pip.git'))

        argv = ['show', '--owner', '--login', 'pypa/pip']
        val = pipgh.show(True, argv, output=False)
        self.assertTrue(val == 'pypa')

