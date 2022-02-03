#!/usr/bin/env python3

from os import makedirs
from typing import List, Optional, Union as TUnion
from gidocgen.gir.ast import (
    ArrayType, Class, GIRElement, Interface, ListType, Type, Union, Record
)
from gidocgen.gir.parser import GirParser
from os.path import isdir


GIR_DIR = '/usr/share/gir-1.0'

TYPE_MAP = {
    'utf8': 'str',
    'filename': 'str',
    'gunichar': 'str',
    'char': 'str',
    'gboolean': 'bool',
    'none': None,
    'double': 'float',
    'float': 'float',
    'int': 'int',
    'guint': 'int',
    'guint8': 'int',
    'guint16': 'int',
    'guint32': 'int',
    'guint64': 'int',
    'gint8': 'int',
    'gint16': 'int',
    'gint32': 'int',
    'gint64': 'int',
    'gsize': 'int',
    'gssize': 'int',
    'long': 'int',
    'GLib.DateDay': 'int',
    'GLib.DateYear': 'int',
    'GLib.TimeSpan': 'int',
    'gpointer': 'object'
}

TYPE_UNKNOWN = '-99999'

LEN_NAME_FRAGMENTS = [
    'n_', 'num_', 'size', 'len'
]


class GSGField:
    def __init__(self, name: str, value: str = '...'):
        self.name = name
        self.value = value

    def to_str(self, indent: int = 1) -> str:
        return (indent * '    ') + f'{self.name} = {self.value}'


class GSGParam:
    def __init__(
            self, name: str, module: str, typ: Optional[str] = None,
            default: Optional[str] = None
    ):
        self.name = name.replace('-', '_')
        self.typ = typ
        if self.typ and f'{module}.' in self.typ:
            self.typ = self.typ.removeprefix(f'{module}.')
        self.default = default
        if self.name == '...':
            self.name = '*args'
            self.typ = None
            self.default = None

    def to_str(self) -> str:
        return self.name + (
            f': {self.typ}' if self.typ else ''
        ) + (
            f' = {self.default}' if self.default else ''
        )


class GSGMethod:
    def __init__(
            self, name: str, params: List[GSGParam], module: str,
            ret_typ: Optional[str] = None, static: bool = False
    ):
        self.name = name + ('_' if name in (
            'continue', 'yield'
        ) else '')
        self.params = params
        self.ret_typ = ret_typ
        if self.ret_typ and f'{module}.' in self.ret_typ:
            self.ret_typ = self.ret_typ.removeprefix(f'{module}.')
        self.static = static

    def to_str(self, indent: int = 1) -> str:
        params = ['cls' if self.static else 'self'] + [
            p.to_str() for p in self.params
        ]
        return (indent * '    ') + (
            ('@classmethod\n' + (indent * '    ')) if self.static else ''
        ) + (
            f'def {self.name}('
        ) + (
            ', '.join(params)
        ) + ')' + (
            f' -> {self.ret_typ}' if self.ret_typ else ''
        ) + ':\n' + ((indent+1) * '    ') + '...'


class GSGClass:
    def __init__(
            self, name: str, methods: List[GSGMethod], module: str,
            ancestors: List[str] = [], fields: List[GSGField] = []
    ):
        self.name = name
        self.methods = methods
        self.module = module
        self.ancestors = [
            anc.removeprefix(f'{module}.') if f'{module}.' in anc else anc
            for anc in ancestors
        ]
        self.fields = fields
        self.manage_special_cases()

    def to_str(self, indent: int = 0) -> str:
        res = (indent * '    ') + f'class {self.name}' + (
            f'({", ".join(self.ancestors)})'
            if len(self.ancestors) > 0 else ''
        ) + ':\n'
        if len(self.methods) <= 0 and len(self.fields) <= 0:
            res += ((indent+1) * '    ') + '...'
            return res
        res += '\n'.join([f.to_str(indent+1) for f in self.fields])
        res += (
            '\n\n' if len(self.fields) > 0 else ''
        ) + '\n\n'.join(
            [m.to_str(indent+1) for m in self.methods]
        )
        return res

    def manage_special_cases(self):
        if self.module == 'GLib':
            if self.name == 'Hook':
                self.methods = [
                    m for m in self.methods
                    if m.name != 'destroy'
                ]
            elif self.name == 'MainContext':
                self.methods = [
                    m for m in self.methods
                    if m.name != 'get_poll_func'
                ]
        if self.module == 'GObject':
            if self.name == 'Object':
                self.methods += [GSGMethod('emit', [
                    GSGParam('signal', self.module, 'str'),
                    GSGParam('*args', self.module)
                ], self.module)]


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

    def type_to_pytype(self, typ: Optional[GIRElement]) -> Optional[str]:
        if not typ:
            return None
        if isinstance(typ, Type):
            if not typ.name:
                return None
            res = TYPE_MAP.get(typ.name, TYPE_UNKNOWN)
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
    ) -> List[GSGMethod]:
        res = list()
        methods = cls.methods
        clsmethods = (
            list(cls.constructors) if not isinstance(cls, Interface) else []
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
                param.name for param in method.parameters if param.name and
                param.name not in ['argc']
            ]
            if return_type and 'Array[' in return_type:
                params = [p for p in params if len([
                    npn for npn in LEN_NAME_FRAGMENTS if npn in p
                ]) <= 0]
                return_type = 'List' + return_type.removeprefix('Array')
            if return_type and 'List[' in return_type:
                return_type = 'Py' + return_type
            res.append(GSGMethod(
                method.name,
                [GSGParam(param, self.libname) for param in params],
                self.libname, return_type
            ))

        # class methods / static methods / constructors / functions
        for method in clsmethods:
            if not method or not method.name:
                continue
            res.append(GSGMethod(
                method.name, [
                    GSGParam(param.name, self.libname)
                    for param in method.parameters if param.name
                ], self.libname, static=True
            ))

        return res

    def gen(self):
        parser = GirParser([GIR_DIR])
        parser.parse(self.girpath)
        repo = parser.get_repository()
        assert(repo is not None and repo.namespace is not None)

        stub = ''
        if len(self.imports) > 0:
            stub += 'from gi.repository import ' + ', '.join(self.imports)
        stub += '\nfrom enum import Enum\n'
        stub += '\nfrom typing import List as PyList\n\n\n'

        gsg_classes = list()

        # classes
        for cls in repo.namespace.get_classes():
            if not cls.name:
                continue
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
            init = GSGMethod(
                '__init__', [
                    GSGParam(prop, self.libname, default='None')
                    for prop in properties
                ], self.libname
            )
            methods = [init] + self.extract_methods(cls)
            cls_o = GSGClass(
                cls.name, methods, self.libname, inherits
            )
            gsg_classes.append(cls_o)

        # unions, records, interfaces
        records = repo.namespace.get_records()
        unions = repo.namespace.get_unions()
        interfaces = repo.namespace.get_interfaces()
        for structs in (records, unions, interfaces):
            for struct in structs:
                if not struct or not struct.name:
                    continue
                struct_o = GSGClass(
                    struct.name, self.extract_methods(struct), self.libname,
                    fields=[
                        GSGField(f.name)
                        for f in struct.fields if f and f.name
                    ]
                )
                gsg_classes.append(struct_o)

        # enums
        enums = list(repo.namespace.get_enumerations())
        enums.extend(repo.namespace.get_bitfields())
        for enum in enums:
            if not enum or not enum.name:
                continue
            enum_o = GSGClass(
                enum.name, [], self.libname, fields=[
                    GSGField(member.name.upper(), member.value)
                    for member in enum.members if member and member.name
                ], ancestors=['Enum']
            )
            gsg_classes.append(enum_o)

        stub += '\n\n\n'.join([cls.to_str() for cls in gsg_classes])
        self.write(stub)


libs = [
    GirLib('GLib-2.0', 'gi.repository.GLib', []),
    GirLib('GObject-2.0', 'gi.repository.GObject', ['GLib']),
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
