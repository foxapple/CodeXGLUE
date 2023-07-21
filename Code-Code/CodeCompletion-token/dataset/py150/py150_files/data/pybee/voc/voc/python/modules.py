import os

from ..java import (
    Class as JavaClass,
    Code as JavaCode,
    Method as JavaMethod,
    opcodes as JavaOpcodes,
    SourceFile,
)
from .blocks import Block, IgnoreBlock
from .methods import MainMethod, Method, CO_GENERATOR, GeneratorMethod, extract_parameters
from .opcodes import ASTORE_name, ALOAD_name, free_name


class StaticBlock(Block):

    def transpile_setup(self):
        self.add_opcodes(
            # JavaOpcodes.LDC_W("STATIC BLOCK OF " + self.module.class_name),
            # JavaOpcodes.INVOKESTATIC('org/Python', 'debug', '(Ljava/lang/String;)V'),

            JavaOpcodes.GETSTATIC('org/python/ImportLib', 'modules', 'Ljava/util/Map;'),
            JavaOpcodes.LDC_W(self.module.descriptor),

            JavaOpcodes.NEW('org/python/types/Module'),
            JavaOpcodes.DUP(),
            JavaOpcodes.LDC_W(self.module.class_name),
            JavaOpcodes.INVOKESTATIC('java/lang/Class', 'forName', '(Ljava/lang/String;)Ljava/lang/Class;'),

            JavaOpcodes.INVOKESPECIAL('org/python/types/Module', '<init>', '(Ljava/lang/Class;)V'),

            JavaOpcodes.INVOKEINTERFACE('java/util/Map', 'put', '(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;'),
            JavaOpcodes.POP()
        )

    def transpile_teardown(self):
        self.add_opcodes(
            JavaOpcodes.RETURN(),
        )

    def store_name(self, name, use_locals):
        self.add_opcodes(
            ASTORE_name(self, '#value'),
            JavaOpcodes.GETSTATIC('org/python/ImportLib', 'modules', 'Ljava/util/Map;'),
            JavaOpcodes.LDC_W(self.module.descriptor),
            JavaOpcodes.INVOKEINTERFACE('java/util/Map', 'get', '(Ljava/lang/Object;)Ljava/lang/Object;'),
            JavaOpcodes.CHECKCAST('org/python/types/Module'),

            JavaOpcodes.LDC_W(name),
            ALOAD_name(self, '#value'),

            JavaOpcodes.INVOKEINTERFACE('org/python/Object', '__setattr__', '(Ljava/lang/String;Lorg/python/Object;)V'),
        )
        free_name(self, '#value')

    def store_dynamic(self):
        self.add_opcodes(
            ASTORE_name(self, '#value'),
            JavaOpcodes.LDC_W(self.module.class_name),
            JavaOpcodes.INVOKESTATIC('org/python/types/Type', 'pythonType', '(Ljava/lang/String;)Lorg/python/types/Type;'),

            JavaOpcodes.GETFIELD('org/python/types/Type', 'attrs', 'Ljava/util/Map;'),

            ALOAD_name(self, '#value'),
            JavaOpcodes.INVOKEINTERFACE('java/util/Map', 'putAll', '(Ljava/util/Map;)V'),
        )
        free_name(self, '#value')

    def load_name(self, name, use_locals):
        self.add_opcodes(
            JavaOpcodes.GETSTATIC('org/python/ImportLib', 'modules', 'Ljava/util/Map;'),
            JavaOpcodes.LDC_W(self.module.descriptor),
            JavaOpcodes.INVOKEINTERFACE('java/util/Map', 'get', '(Ljava/lang/Object;)Ljava/lang/Object;'),
            JavaOpcodes.CHECKCAST('org/python/types/Module'),
            JavaOpcodes.LDC_W(name),
            JavaOpcodes.INVOKEINTERFACE('org/python/Object', '__getattribute__', '(Ljava/lang/String;)Lorg/python/Object;'),
        )

    def delete_name(self, name, use_locals):
        self.add_opcodes(
            JavaOpcodes.GETSTATIC('org/python/ImportLib', 'modules', 'Ljava/util/Map;'),
            JavaOpcodes.LDC_W(self.module.descriptor),
            JavaOpcodes.INVOKEINTERFACE('java/util/Map', 'get', '(Ljava/lang/Object;)Ljava/lang/Object;'),
            JavaOpcodes.CHECKCAST('org/python/types/Module'),
            JavaOpcodes.LDC_W(name),
            JavaOpcodes.INVOKEVIRTUAL('org/python/types/Module', '__delattr__', '(Ljava/lang/String;)Lorg/python/Object;'),
        )

    @property
    def descriptor(self):
        return self.parent.descriptor

    @property
    def module(self):
        return self.parent

    def add_method(self, method_name, code, annotations):
        if code.co_flags & CO_GENERATOR:
            # Generator method.
            method = GeneratorMethod(
                self.module,
                generator=code.co_name,
                name=method_name,
                parameters=extract_parameters(code, annotations),
                returns={
                    'annotation': annotations.get('return', 'org.python.Object').replace('.', '/')
                },
                static=True,
                verbosity=self.module.verbosity
            )
        else:
            # Normal method.
            method = Method(
                self.module,
                name=method_name,
                parameters=extract_parameters(code, annotations),
                returns={
                    'annotation': annotations.get('return', 'org.python.Object').replace('.', '/')
                },
                static=True,
                verbosity=self.module.verbosity
            )
        method.extract(code)
        self.module.methods.append(method)
        return method


class Module(Block):
    def __init__(self, namespace, sourcefile, verbosity=0):
        super().__init__(verbosity=verbosity)
        self.sourcefile = sourcefile

        parts = os.path.splitext(sourcefile)[0].split(os.path.sep)
        if parts[-1] == '__init__':
            parts.pop()

        # If the sourcefile started with a /, the first part will
        # be an empty string; replace that with the namespace.
        # Otherwise, prepend the namespace to the parts.
        if parts[0] == '':
            parts[0] = namespace
        else:
            parts = [namespace] + parts
        self.namespace = '.'.join(parts[:-1])
        self.name = parts[-1]

        self.methods = []
        self.classes = []
        self.anonymous_inner_class_count = 0

    @property
    def descriptor(self):
        return '/'.join(self.namespace.split('.') + [self.name])

    @property
    def class_name(self):
        return '.'.join(self.namespace.split('.') + [self.name, '__init__'])

    @property
    def class_descriptor(self):
        return '/'.join(self.namespace.split('.') + [self.name, '__init__'])

    def materialize(self):
        "Convert a collection of commands into a full Python code definition"
        main_commands = []
        body_commands = []
        main_end = None

        main = None

        for cmd in self.commands:
            if main_end is not None:
                # Marker for the end of the main block:
                if cmd.is_main_end(main_end):
                    try:
                        main = MainMethod(self, main_commands, end_offset=main_end, verbosity=self.verbosity)
                    except IgnoreBlock:
                        pass
                    main_end = None
                else:
                    main_commands.append(cmd)
            else:
                # Look for a very specific pattern, flagging the "main" method:
                #   if __name__ == '__main__':
                #       ...
                # which is represented as:
                #         LOAD_NAME: __name__
                #         LOAD_CONST: __main__
                #     COMPARE_OP: ==
                #  POP_JUMP_IF_FALSE: <end of block target>
                #  ... <main code>
                #  <end of block target>
                if cmd.is_main_start():
                    if main is not None:
                        print("Found duplicate main block... replacing previous main")

                    main_end = cmd.operation.target

                # All other module-level cmds goes into the static block
                else:
                    body_commands.append(cmd)

        # Create the body of the module definition
        self.body = StaticBlock(self, body_commands)

        if main is None:
            if self.verbosity:
                print("Adding default main method...")
            main = MainMethod(self, [], verbosity=self.verbosity)

        self.methods.append(main)

        # Having constructed all the parts of the module, materialize them.
        self.body.materialize()

        for method in self.methods:
            method.materialize()

        for klass in self.classes:
            klass.materialize()

    def transpile(self):
        """Convert a materialized Python code definition into a list of Java
        Classfile definitions.

        Returns a list of triples:
            (namespace, class_name, javaclassfile)

        The list contains the classfile for the module, plus and classes
        defined in the module.
        """
        # If there is any static content, generate a classfile
        # for this module
        classfile = JavaClass(self.class_descriptor, extends='org/python/types/Module')
        classfile.attributes.append(SourceFile(os.path.basename(self.sourcefile)))

        # Add a static method to the module, populated with the
        # body content of the module.
        static_init = JavaMethod('<clinit>', '()V', public=False, static=True)
        static_init.attributes.append(self.body.transpile())
        classfile.methods.append(static_init)

        # Add a dummy init method.
        classfile.methods.append(
            JavaMethod(
                '<init>',
                '()V',
                attributes=[
                    JavaCode(
                        max_stack=1,
                        max_locals=1,
                        code=[
                            JavaOpcodes.ALOAD_0(),
                            JavaOpcodes.INVOKESPECIAL('org/python/types/Module', '<init>', '()V'),
                            JavaOpcodes.RETURN(),
                        ],
                    ),
                ]
            )
        )

        # Add any static methods defined in the module
        for method in self.methods:
            classfile.methods.extend(method.transpile())

        # The list of classfiles that will be returned will contain
        # at least one entry - the class for the module itself.
        classfiles = [(
            self.namespace,
            '%s/__init__' % self.name,
            classfile
        )]
        # Also output any classes defined in this module.
        for klass in self.classes:
            classfiles.append(klass.transpile())

        return classfiles
