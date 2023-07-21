import os, time, errno
from test import *
from fsmonitor import *

try:
    test.add_dir_watch("/this/path/does/not/exist")
except FSMonitorError as e:
    assert e.errno == errno.ENOENT
else:
    assert False, "Expected exception"
