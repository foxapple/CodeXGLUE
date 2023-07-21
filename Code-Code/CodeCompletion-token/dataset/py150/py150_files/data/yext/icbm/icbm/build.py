#!/usr/bin/python2.7

import ConfigParser
import optparse
import os
import re
import sys
import time

import engine
import data
import genautodep


APPDIR_RE = re.compile(r"(/app)($|/)")

def RegisterJavaLibrary(module, f):
    name = "lib%s" % f.name
    lib = data.JavaLibrary(
        module.name, f.path, name,
        list(data.FixPath(module.name, f.path, ["%s.java" % f.name])),
        [],
        list(c.DepName() for c in f.classes),
        [])
    data.DataHolder.Register(module.name, f.path, name, lib)
    #print "reg %s=%s:%s" % (module.name, f.path, name)

    # Create a binary target that depends solely on the lib
    binary = data.JavaBinary(
        module.name, f.path, f.name,
        "%s/%s" % (f.path, f.name),
        ["%s:%s" % (f.path, name)])
    data.DataHolder.Register(module.name, f.path, f.name, binary)

    # Create a jar target for the binary as well
    jar = data.JavaJar(
        module.name, f.path, f.name + "_deploy", binary.FullName())
    data.DataHolder.Register(module.name, f.path, f.name + "_deploy", jar)


def main():
    start_time = time.time()

    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    (options, args) = parser.parse_args()
    data.VERBOSE = options.verbose

    config = ConfigParser.SafeConfigParser(allow_no_value=True)
    # Module paths (the options of the modules section) must be case sensitive.
    config.optionxform = str
    config.read("icbm.cfg")
    if config.has_section("modules"):
        module_paths = [path for path, _ in config.items("modules")]
    else:
        module_paths = ["lib", "src"]
    if config.has_option("java", "flags_by_default"):
        data.JAVA_BINARY_FLAGS_DEFAULT = config.getboolean(
            "java", "flags_by_default")
    if config.has_option("proto", "protobuf_java"):
        protobuf_java = config.get("proto", "protobuf_java")
    else:
        protobuf_java = "lib=:protobuf-java-2.5.0"

    try:
        os.mkdir(engine.BUILD_DIR)
    except:
        pass

    modules = genautodep.ComputeDependencies(module_paths)

    for module in modules.itervalues():
        mname = module.name
        app_dirs = {}
        for package, farr in module.files.iteritems():
            # Process non-protos before protos, in case there is
            # already a checked-in version, so that they don't
            # conflict.
            filemap = {}

            java_files = []
            proto_files = []
            for f in farr:
                if mname == "src":
                    m = APPDIR_RE.search(f.path)
                    if m:
                        appdir = f.path[:m.end(1)]
                        app_dirs.setdefault(appdir, []).append(f)
                        # We want to allow tests to depend on these,
                        # so keep processing as usual. In the future,
                        # some sort of compromise will need to be
                        # made, as this can still lead to namespace collisions.
                        #continue
                filemap.setdefault(f.path, []).append(f)
                if isinstance(f, genautodep.ProtoFile):
                    proto_files.append(f)
                else:
                    java_files.append(f)

            for f in java_files:
                RegisterJavaLibrary(module, f)

            for f in proto_files:
                # Skip protos if there's already a lib for that name
                # that is out there.
                if data.DataHolder.Get(mname, f.DepName()):
                    continue

                RegisterJavaLibrary(module, f)
                # Autodep doesn't find the dependency on protobufs.
                data.DataHolder.Get(mname, f.DepName()).deps.append(
                    protobuf_java)

                gen = data.Generate(
                    mname, f.path, f.name + "_proto",
                    "%s/genproto.sh" % engine.ICBM_PATH, None,
                    list(data.FixPath(mname, f.path, ["%s.proto" % f.protoname])) + f.extras,
                    [os.path.join(f.path, "%s.java" % f.name)])
                data.DataHolder.Register(mname, f.path, f.name + "_proto", gen)

            # Create a lib in each package as well
            for path, file_arr in filemap.iteritems():
                lib = data.JavaLibrary(
                    mname, path, "lib",
                    [],
                    [],
                    list(f.DepName() for f in file_arr),
                    [])
                data.DataHolder.Register(mname, path, "lib", lib)

        for path, file_arr in app_dirs.iteritems():
            deps = set()
            for f in file_arr:
                for c in f.classes:
                    if not APPDIR_RE.search(c.path):
                        deps.add(c.DepName())
            lib = data.JavaLibrary(
                mname, path, "app_deps",
                [],
                [],
                list(deps),
                [])
            data.DataHolder.Register(mname, path, "app_deps", lib)

        for jar in module.jars:
            lib = data.JavaLibrary(
                mname, "", jar.name, [],
                list(data.FixPath(mname, jar.path, ["%s.jar" % jar.name])),
                [], [])
            data.DataHolder.Register(mname, jar.path, jar.name, lib)
        lib = data.JavaLibrary(
            mname, "", "jars",
            [],
            [],
            list(f.DepName() for f in module.jars),
            [])
        data.DataHolder.Register(mname, "", "jars", lib)

        if module.jsps:
            lib = data.JavaLibrary(
                mname, "", "jsp_deps",
                [],
                [],
                list(c.DepName() for jsp in module.jsps for c in jsp.classes),
                [])
            data.DataHolder.Register(mname, "", "jsp_deps", lib)

    for target in args:
        # load the corresponding spec files
        data.LoadTargetSpec(data.TOPLEVEL, target)
    for target in args:
        d = data.DataHolder.Get(data.TOPLEVEL, target)
        if not d:
            print "Unknown target:", target
            sys.exit(1)
        d.LoadSpecs()
    success = data.DataHolder.Go(args)

    elapsed_time = time.time() - start_time
    print
    print "Total ICBM build time: %.1f seconds" % elapsed_time

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
