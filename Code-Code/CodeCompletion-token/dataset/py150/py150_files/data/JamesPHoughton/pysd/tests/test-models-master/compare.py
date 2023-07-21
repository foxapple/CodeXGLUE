#!/usr/bin/env python

import cmath
import csv
import re
import sys

# these columns are either Vendor specific or otherwise not important.
IGNORABLE_COLS = ('saveper', 'initial_time', 'final_time', 'time_step')

# from rainbow
def make_reporter(verbosity, quiet, filelike):
    "Returns a function suitible for logging use."
    if not quiet:
        def report(level, msg, *args):
            "Log if the specified severity is <= the initial verbosity."
            if level <= verbosity:
                if len(args):
                    filelike.write(msg % args + '\n')
                else:
                    filelike.write('%s\n' % (msg,))
    else:
        def report(level, msg, *args):
            "/dev/null logger."
            pass
    return report

ERROR = 0
WARN = 1
INFO = 2
DEBUG = 3
log = make_reporter(DEBUG, False, sys.stderr)

def isclose(a,
            b,
            rel_tol=1e-9,
            abs_tol=0.0,
            method='weak'):
    """
    returns True if a is close in value to b. False otherwise
    :param a: one of the values to be tested
    :param b: the other value to be tested
    :param rel_tol=1e-8: The relative tolerance -- the amount of error
                         allowed, relative to the magnitude of the input
                         values.
    :param abs_tol=0.0: The minimum absolute tolerance level -- useful for
                        comparisons to zero.
    :param method: The method to use. options are:
                  "asymmetric" : the b value is used for scaling the tolerance
                  "strong" : The tolerance is scaled by the smaller of
                             the two values
                  "weak" : The tolerance is scaled by the larger of
                           the two values
                  "average" : The tolerance is scaled by the average of
                              the two values.
    NOTES:
    -inf, inf and NaN behave similar to the IEEE 754 standard. That
    -is, NaN is not close to anything, even itself. inf and -inf are
    -only close to themselves.
    Complex values are compared based on their absolute value.
    The function can be used with Decimal types, if the tolerance(s) are
    specified as Decimals::
      isclose(a, b, rel_tol=Decimal('1e-9'))
    See PEP-0485 for a detailed description

    Copyright: Christopher H. Barker
    License: Apache License 2.0 http://opensource.org/licenses/apache2.0.php
    """
    if method not in ("asymmetric", "strong", "weak", "average"):
        raise ValueError('method must be one of: "asymmetric",'
                         ' "strong", "weak", "average"')

    if rel_tol < 0.0 or abs_tol < 0.0:
        raise ValueError('error tolerances must be non-negative')

    if a == b:  # short-circuit exact equality
        return True
    # use cmath so it will work with complex or float
    if cmath.isinf(a) or cmath.isinf(b):
        # This includes the case of two infinities of opposite sign, or
        # one infinity and one finite number. Two infinities of opposite sign
        # would otherwise have an infinite relative tolerance.
        return False
    diff = abs(b - a)
    if method == "asymmetric":
        return (diff <= abs(rel_tol * b)) or (diff <= abs_tol)
    elif method == "strong":
        return (((diff <= abs(rel_tol * b)) and
                 (diff <= abs(rel_tol * a))) or
                (diff <= abs_tol))
    elif method == "weak":
        return (((diff <= abs(rel_tol * b)) or
                 (diff <= abs(rel_tol * a))) or
                (diff <= abs_tol))
    elif method == "average":
        return ((diff <= abs(rel_tol * (a + b) / 2) or
                 (diff <= abs_tol)))
    else:
        raise ValueError('method must be one of:'
                         ' "asymmetric", "strong", "weak", "average"')

def slurp(file_name):
    with open(file_name, 'r') as f:
        return f.read().strip()

def load_csv(f, delimiter=','):
    result = []
    reader = csv.reader(f, delimiter=delimiter)
    header = next(reader)
    for i in range(len(header)):
        result.append([header[i]])
    for row in reader:
        for i in range(len(row)):
            result[i].append(row[i])
    series = {}
    for i in range(len(result)):
        series[result[i][0]] = result[i][1:]
    return series

NAME_RE = re.compile(' +')

def e_name(n):
    return NAME_RE.sub('_', n)

def read_data(data):
    ins = data.lower().splitlines()
    ins[0] = e_name(ins[0].strip())
    if ',' in ins[0]:
        delimiter = ','
    else:
        delimiter = '\t'
    return load_csv(ins, delimiter)

def compare(reference, simulated, display_limit=-1):
    '''
    Compare two data files for equivalence.
    '''
    time = reference['time']
    steps = len(time)
    err = False
    displayed = 0
    for i in range(steps):
        for n, series in list(reference.items()):
            if n not in simulated:
                if n in IGNORABLE_COLS:
                    continue
                if display_limit >= 0 and displayed < display_limit:
                    log(ERROR, 'missing column %s in second file', n)
                    displayed += 1
                break
            if len(reference[n]) != len(simulated[n]):
                if display_limit >= 0 and displayed < display_limit:
                    log(ERROR, 'len mismatch for %s (%d vs %d)',
                        n, len(reference[n]), len(simulated[n]))
                    displayed += 1
                err = True
                break
            ref = float(series[i])
            sim = float(simulated[n][i])
            around_zero = isclose(ref, 0, abs_tol=1e-06) and isclose(sim, 0, abs_tol=1e-06)
            if not around_zero and not isclose(ref, sim, rel_tol=1e-4):
                if display_limit >= 0 and displayed < display_limit:
                    log(ERROR, 'time %s mismatch in %s (%s != %s)', time[i], n, ref, sim)
                    displayed += 1
                err = True
    return err

def main():
    ref = read_data(slurp(sys.argv[1]))
    sim = read_data(slurp(sys.argv[2]))
    compare(ref, sim)
    return

if __name__ == '__main__':
    exit(main())
