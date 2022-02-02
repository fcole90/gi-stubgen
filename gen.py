#!/usr/bin/env python3

from os import makedirs
from typing import List, Optional, Union as TUnion
from gidocgen.gir.ast import (
    ArrayType, Class, GIRElement, Interface, ListType, Type, Union, Record
)
from gidocgen.gir.parser import GirParser
from os.path import isdir


GIR_DIR = '/usr/share/gir-1.0'

TYPES_MAP = {
    'utf8': 'str',
    'filename': 'str',
    'gunichar': 'str',
    'gboolean': 'bool',
    'none': None,
    'double': 'float',
    'float': 'float',
    'int': 'int',
    'guint': 'int',
    'guint8': 'int',
    'guint16': 'int',
    'gint8': 'int',
    'gint16': 'int',
    'gint64': 'int',
    'gsize': 'int',
    'gssize': 'int',
}

TYPE_UNKNOWN = '-99999'

LEN_NAME_FRAGMENTS = [
    'n_', 'num_', 'size', 'len'
]


class GirLib:
    def __init__(self, girname: str, package: str, imports: List[str] = []):
        # IE: 'Gtk-4.0'
        self.girname = girname
        self.girpath = f'{GIR_DIR}/{self.girname}.gir'
        # IE: 'gi.repository.Gtk'
        self.package = package
        self.libname = self.package.split('.')[-1]
        # IE: ['Gdk', 'Gio', 'GLib']
        self.imports = imports

        self.dest_dir = './out/' + '/'.join(self.package.split('.')[:-1])
        self.dest = f'{self.dest_dir}/{self.libname}.pyi'

    def write(self, stub: str):
        if not isdir(self.dest_dir):
            makedirs(self.dest_dir)
        with open(self.dest, 'w') as fd:
            fd.write(stub)

    def type_to_pytype(self, typ: Optional[GIRElement], dbg=False) -> Optional[str]:
        if not typ:
            return None
        if isinstance(typ, Type):
            if not typ.name:
                return None
            res = TYPES_MAP.get(typ.name, TYPE_UNKNOWN)
            if res == TYPE_UNKNOWN:
                if f'{self.libname}.' in typ.name:
                    return typ.name.removeprefix(f'{self.libname}.')
                return typ.name
            return res
        elif isinstance(typ, ArrayType):
            return f'Array[{self.type_to_pytype(typ.value_type)}]'
        elif isinstance(typ, ListType):
            return f'List[{self.type_to_pytype(typ.value_type)}]'

    def extract_methods(
            self, cls: TUnion[Class, Union, Interface, Record]
    ) -> str:
        stub = ''
        methods = cls.methods
        clsmethods = (
            list(cls.constructors) if hasattr(cls, 'constructors') else []
        )
        clsmethods.extend(cls.functions)
        # methods
        for method in methods:
            if not method or not method.name:
                continue
            return_type = self.type_to_pytype(
                method.return_value.target
                if method.return_value else None
            )
            params = [
                ('*args' if param.name == '...' else param.name)
                for param in method.parameters if param.name and
                param.name not in ['argc']
            ]
            if return_type and 'Array[' in return_type:
                params = [p for p in params if len([
                    npn for npn in LEN_NAME_FRAGMENTS if npn in p
                ]) <= 0]
                return_type = 'List' + return_type.removeprefix('Array')
            stub += '    def ' + (
                method.name if method.name != 'continue' else 'continue_'
            )
            stub += '(self, ' + ', '.join(params) + ')'
            if return_type:
                stub += ' -> ' + return_type
            stub += ':\n'
            stub += '        ...\n\n'

        # class methods / static methods / constructors / functions
        for method in clsmethods:
            if not method or not method.name:
                continue
            if method.name == 'continue':
                continue
            stub += '    @classmethod\n'
            stub += '    def ' + method.name + '(cls, ' + ', '.join([
                ('*args' if param.name == '...' else param.name)
                for param in method.parameters if param.name
            ]) + '):\n'
            stub += '        ...\n\n'

        stub += '\n\n'
        return stub

    def gen(self):
        parser = GirParser([GIR_DIR])
        parser.parse(self.girpath)
        repo = parser.get_repository()
        assert(repo is not None and repo.namespace is not None)

        stub = ''
        if len(self.imports) > 0:
            stub += 'from gi.repository import ' + ', '.join(self.imports)
        stub += '\nfrom typing import List\n\n\n'

        # classes
        for cls in repo.namespace.get_classes():
            if not cls.name:
                continue
            stub += 'class '
            # for multiple inheritance
            # stub += cls.name + '(' + ', '.join([anc.name for anc in cls.ancestors]) + ')'
            stub += cls.name
            properties = list(cls.properties.keys())
            inherits = []
            if len(cls.ancestors) > 0:
                assert(isinstance(cls.ancestors[0], Class))
                properties.extend(cls.ancestors[0].properties.keys())
                inherits.append(cls.ancestors[0].name)
            for iface in cls.implements:
                assert(isinstance(iface, Interface))
                properties.extend(iface.properties.keys())
                inherits.append(iface.name)
            properties = [prop.replace('-', '_') for prop in properties]
            if len(inherits) > 0:
                stub += '(' + ', '.join(inherits) + '):\n'
            else:
                stub += ':\n'
            stub += '    def __init__(self, ' + ', '.join([
                f'{prop}=None' for prop in properties
            ]) + '):\n        ...\n\n'
            stub += self.extract_methods(cls)
            if cls.name == 'Object' and self.libname == 'GObject':
                stub += '    def emit(self, signal: str, *args):\n'
                stub += '        ...\n\n'

        # unions, records, interfaces
        records = repo.namespace.get_records()
        unions = repo.namespace.get_unions()
        interfaces = repo.namespace.get_interfaces()
        for structs in (records, unions, interfaces):
            for struct in structs:
                if not struct or not struct.name:
                    continue
                stub += f'class {struct.name}:\n'
                if (
                        len(struct.fields) <= 0 and
                        len(struct.methods) <= 0 and
                        (
                            not hasattr(struct, 'constructors') or
                            len(struct.constructors) <= 0
                        ) and
                        len(struct.functions) <= 0
                ):
                    stub += '    ...\n\n'
                    continue
                # fields
                for field in struct.fields:
                    if not field or not field.name:
                        continue
                    stub += '    ' + field.name + ' = ...\n'
                # methods
                stub += self.extract_methods(struct)

        # enums
        enums = list(repo.namespace.get_enumerations())
        enums.extend(repo.namespace.get_bitfields())
        for enum in enums:
            if not enum or not enum.name:
                continue
            stub += 'class ' + enum.name + ':\n'
            for member in enum.members:
                stub += f'    {member.name.upper()} = {member.value}\n'
            stub += '\n\n'

        self.write(stub)


libs = [
    GirLib('GObject-2.0', 'gi.repository.GObject', []),
    GirLib('GLib-2.0', 'gi.repository.GLib', ['GObject']),
    GirLib('Gio-2.0', 'gi.repository.Gio', ['GObject', 'GLib']),
    GirLib('Pango-1.0', 'gi.repository.Pango', ['GObject']),
    GirLib('Gdk-4.0', 'gi.repository.Gdk', ['Gio', 'GLib', 'GObject']),
    GirLib('GdkPixbuf-2.0', 'gi.repository.GdkPixbuf', [
        'Gdk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('Gtk-4.0', 'gi.repository.Gtk', [
        'Gdk', 'Gio', 'GLib', 'GObject', 'Pango'
    ]),
    GirLib('Adw-1', 'gi.repository.Adw', [
        'Gdk', 'Gtk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('WebKit2-5.0', 'gi.repository.WebKit2', [
        'Gtk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('GtkSource-5', 'gi.repository.GtkSource', [
        'Gtk', 'Gio', 'GLib', 'GObject'
    ]),
]
for lib in libs:
    lib.gen()
