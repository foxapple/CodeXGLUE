# -*- coding: utf-8 -*-
import os
from click.testing import CliRunner
from easy_karabiner import util
from easy_karabiner import __version__
from easy_karabiner.__main__ import *


def test_main():
    inpath = 'samples/basic.py'
    outpath = 'samples/basic.xml'

    configs = read_config_file(inpath)
    assert(len(configs['REMAPS']) > 0)

    xml_str = gen_config(configs)
    with open(outpath, 'r') as fp:
        util.assert_xml_equal(fp.read(), xml_str, ignore_tags=['Easy-Karabiner'])

    write_generated_xml(outpath, xml_str)
    newpath = backup_file(outpath)
    os.rename(newpath, outpath)

    args = [inpath, outpath, '--verbose', '--string', '--no-reload']
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert(result.exit_code == 0)