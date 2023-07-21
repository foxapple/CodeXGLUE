import pytest
import os.path
import fs

from .setup import *

def test_rm_file():
    if (not os.path.exists(TEST_FILE)):
        raise ValueError("File %s does not exist!" % TEST_FILE)

    fs.rm(TEST_FILE)

    assert os.path.exists(TEST_FILE) is False