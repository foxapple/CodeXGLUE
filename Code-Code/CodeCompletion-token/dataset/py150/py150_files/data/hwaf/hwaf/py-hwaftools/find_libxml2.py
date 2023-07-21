# -*- python -*-

# stdlib imports ---
import os
import os.path as osp

# waf imports ---
import waflib.Utils
import waflib.Logs as msg
from waflib.Configure import conf

#
_heptooldir = osp.dirname(osp.abspath(__file__))

def options(opt):
    opt.load('hwaf-base', tooldir=_heptooldir)
    opt.add_option(
        '--with-libxml2',
        default=None,
        help="Look for LibXML2 at the given path")
    return

def configure(conf):
    conf.load('hwaf-base', tooldir=_heptooldir)
    return

@conf
def find_libxml2(ctx, **kwargs):
    
    if not ctx.env.HWAF_FOUND_C_COMPILER:
        ctx.fatal('load a C compiler first')
        pass

    if not ctx.env.HWAF_FOUND_CXX_COMPILER:
        ctx.fatal('load a C++ compiler first')
        pass


    # find LibXML2
    xml_cfg = "xml2-config"
    path_list = waflib.Utils.to_list(kwargs.get('path_list', []))
    if getattr(ctx.options, 'with_libxml2', None):
        topdir = ctx.options.with_libxml2
        topdir = ctx.hwaf_subst_vars(topdir)
        path_list.append(osp.abspath(osp.join(topdir, "bin")))
        pass
    kwargs['path_list'] = path_list
    
    ctx.find_program(
        xml_cfg,
        var='LIBXML2-CONFIG',
        **kwargs)
    #xml_cfg = ctx.env['LIBXML2-CONFIG']
    
    ctx.check_with(
        ctx.check_cfg,
        "xml2",
        path=xml_cfg,
        package="",
        uselib_store="libxml2",
        args='--cflags --libs',
        **kwargs)

    version = ctx.check_cxx(
        msg="Checking xml2 version",
        okmsg="ok",
        fragment='''\
        #include "libxml/xmlversion.h"
        #include <iostream>

        int main(int argc, char* argv[]) {
          std::cout << LIBXML_DOTTED_VERSION;
          return 0;
        }
        ''',
        use="libxml2",
        define_name = "HWAF_LIBXML2_VERSION",
        define_ret = True,
        execute  = True,
        mandatory=True,
        )
    ctx.start_msg("libxml2 version")
    ctx.end_msg(version)

    ctx.env.LIBXML2_VERSION = version
    ctx.env.HWAF_FOUND_LIBXML2 = 1
    return

## EOF ##
