import logging
import os
import re
import sys

from nose.plugins import Plugin

from base import Knows


def modname(qualname):
    candidate = qualname[0]
    for elem in qualname[1:]:
        if ".".join((candidate, elem)) not in sys.modules:
            return candidate
        candidate = ".".join((candidate, elem))

# nose generates two types of test names: unittest-based test cases
# are named "Test(<module.class testMethod=method>"). Non-unittest
# test cases (functions and methods) simply have a dotted name like
# "Test(module.class.method)".
TESTMETH = re.compile(r"Test\(\<(?P<class>[\w_\.]+) "
                      "testMethod=(?P<method>[\w_]+)\>\)")
TESTFUNC = re.compile(r"Test\((?P<func>[\w_\.]+)\)")


def parse_test_name(test_name):
    # Try to match both name styles we know.
    mo = TESTMETH.match(test_name)
    if mo:
        qualname = mo.groupdict()["class"].split(".")
        method_name = mo.groupdict()["method"]
        module_name = ".".join(qualname[:-1])
        class_name = qualname[-1]
        return "%s:%s.%s" % (module_name, class_name, method_name)
    mo = TESTFUNC.match(test_name)
    if mo:
        qualname = mo.groupdict()["func"].split(".")
        module_name = modname(qualname)
        func_name = qualname[-1]
        return "%s:%s" % (module_name, func_name)
    # No match
    return ''


class KnowsNosePlugin(Plugin):
    name = 'knows'

    def __init__(self, *args, **kwargs):
        self.output = True
        self.enableOpt = 'with-knows'
        self.logger = logging.getLogger('nose.plugins.knows')

    def options(self, parser, env=os.environ):
        parser.add_option(
            '--knows-file',
            type='string',
            dest='knows_file',
            default='.knows',
            help='Output file for knows plugin.',
        )
        parser.add_option(
            '--knows-out',
            action='store_true',
            dest='knows_out',
            help='Whether to output the mapping of files to unit tests.',
        )
        parser.add_option(
            '--knows-dir',
            type='string',
            dest='knows_dir',
            default='',
            help='Include only this given directory. This should be your '
                 'project directory name, and does not need to be an absolute '
                 'path.',

        )
        parser.add_option(
            '--knows-exclude',
            type='string',
            action='append',
            dest='knows_exclude',
            help='Exclude files having this string (can use multiple times).',
        )
        super(KnowsNosePlugin, self).options(parser, env=env)

    def configure(self, options, config):
        self.enabled = getattr(options, self.enableOpt)
        if self.enabled:
            self.knows = Knows(
                knows_filename=options.knows_file,
                output=options.knows_out,
                knows_directory=options.knows_dir,
                exclude=options.knows_exclude,
            )
            input_files = config.testNames
            if not options.knows_out:
                if input_files:
                    config.testNames = self.knows.get_tests_to_run(
                        input_files,
                    )

        super(KnowsNosePlugin, self).configure(options, config)

    def begin(self):
        self.knows.begin()

    def startTest(self, test):
        self.knows.start_test(parse_test_name(repr(test)))

    def stopTest(self, test):
        self.knows.stop_test(parse_test_name(repr(test)))

    def finalize(self, result):
        self.knows.finalize()
