#!/usr/bin/env python3

import importlib
import inspect
from os import makedirs
from typing import List, Optional, Union as TUnion
from gidocgen.gir.ast import (
    ArrayType, Class, GIRElement, Interface, ListType, Type, Union, Record
)
from gidocgen.gir.parser import GirParser
from os.path import isdir
import gi


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
    def __init__(
            self, name: str, value: str = '...', typ: Optional[str] = None
    ):
        self.name = name
        self.value = value
        self.typ = typ

    def to_str(self, indent: int = 1) -> str:
        return (indent * '    ') + '{0}{1} = {2}'.format(
            self.name,
            f': {self.typ}' if self.typ else '',
            self.value
        )


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
        elif (
                self.name in (
                    'user_data', 'user_data_free_func', 'user_destroy'
                )
                and self.default is None
        ):
            self.default = 'None'

    def to_str(self) -> str:
        return self.name + (
            f': {self.typ}' if self.typ else ''
        ) + (
            f' = {self.default}' if self.default else ''
        )


class GSGFunction:
    def __init__(
        self, name: str, params: List[GSGParam], module: str,
        ret_typ: Optional[str] = None
    ):
        self.name = name + ('_' if name in (
            'continue', 'yield'
        ) else '')
        self.params = params
        self.ret_typ = ret_typ
        if self.ret_typ and f'{module}.' in self.ret_typ:
            self.ret_typ = self.ret_typ.removeprefix(f'{module}.')

    def to_str(self, indent: int = 0) -> str:
        return (indent * '    ') + (
            f'def {self.name}('
        ) + ', '.join([p.to_str() for p in self.params]) + ')' + (
            f' -> {self.ret_typ}' if self.ret_typ else ''
        ) + ':\n' + ((indent+1) * '    ') + '...'


class GSGMethod(GSGFunction):
    def __init__(
            self, name: str, params: List[GSGParam], module: str,
            ret_typ: Optional[str] = None, static: bool = False
    ):
        self.static = static
        params.insert(0, GSGParam(
            'cls' if self.static else 'self', module
        ))
        super().__init__(name, params, module, ret_typ)

    def to_str(self, indent: int = 1) -> str:
        return (
            ((indent * '    ') + '@classmethod\n') if self.static else ''
        ) + super().to_str(indent)


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
        if self.module == 'Gio':
            if self.name == 'ListModel':
                self.methods += [GSGMethod('__iter__', [], self.module)]
        if self.module == 'GObject':
            if self.name == 'Object':
                self.methods += [GSGMethod('emit', [
                    GSGParam('signal', self.module, 'str'),
                    GSGParam('*args', self.module)
                ], self.module)]


class GirLib:
    def __init__(
            self, girname: str, package: str, imports: List[str] = [],
            additional_code: str = ''
    ):
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

        self.additional_code = additional_code

        gi.require_version(self.libname, self.girname.split('-')[-1])
        self.module = importlib.import_module(
            f'.{self.libname}', 'gi.repository'
        )

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

    def get_py_args(
            self, py_members: list, method_name: str
    ) -> Optional[List[str]]:
        py_methods = [
            t[1] for t in py_members
            if isinstance(t, tuple) and
            t[0] == method_name
        ]
        if len(py_methods) <= 0:
            print(
                f'Error: method {method_name} not found'
            )
            return None
        py_method = py_methods[0]
        py_args = None
        try:
            argspec = inspect.getfullargspec(py_method)
            py_args = argspec.args
            if argspec.varargs:
                py_args.append('*args')
            if argspec.varkw:
                py_args.append('**kwargs')
        except Exception:
            try:
                py_args = [
                    arg.get_name() for arg in py_method.get_arguments()
                ]
            except Exception:
                print(
                    'Error: cannot list arguments for method {method_name}'
                )
        return py_args

    def extract_methods(
            self, cls: TUnion[Class, Union, Interface, Record]
    ) -> List[GSGMethod]:
        assert(cls and cls.name)
        res = list()
        try:
            py_cls = getattr(self.module, cls.name)
        except AttributeError:
            print(
                f'Error: can\'t find class {cls.name} '
                f'in module {self.libname}'
            )
            return []
        py_members = inspect.getmembers(py_cls)
        methods = cls.methods
        clsmethods = (
            list(cls.constructors) if not isinstance(cls, Interface) else []
        )
        clsmethods.extend(cls.functions)
        # methods
        for method in methods:
            if not method or not method.name:
                continue
            py_args = self.get_py_args(py_members, method.name)
            return_type = self.type_to_pytype(
                method.return_value.target
                if method.return_value else None
            )
            params = [
                param for param in method.parameters if param.name and
                (not py_args or param.name in py_args)
            ]
            if return_type and 'Array[' in return_type:
                params = [p for p in params if p.name and len([
                    npn for npn in LEN_NAME_FRAGMENTS if npn in p.name
                ]) <= 0]
                return_type = 'List' + return_type.removeprefix('Array')
            if return_type and 'List[' in return_type:
                return_type = 'Py' + return_type
            gsg_params = [
                GSGParam(
                    p.name, self.libname,
                    typ=('Optional[Any]' if p.nullable else None),
                    default=('None' if p.optional else None)
                ) for p in params if p.name
            ]
            if py_args:
                for extra in ('*args', '**kwargs'):
                    if extra in py_args and extra not in [
                            p.name for p in gsg_params
                    ]:
                        gsg_params.append(GSGParam(extra, self.libname))
            res.append(GSGMethod(
                method.name, gsg_params,
                self.libname, return_type
            ))

        # class methods / static methods / constructors / functions
        for method in clsmethods:
            if not method or not method.name:
                continue
            py_args = self.get_py_args(py_members, method.name)
            gsg_params = [
                GSGParam(
                    p.name, self.libname,
                    typ=('Optional[Any]' if p.nullable else None),
                    default=('None' if p.optional else None)
                )
                for p in method.parameters if p.name and
                (not py_args or p.name in py_args)
            ]
            if py_args:
                for extra in ('*args', '**kwargs'):
                    if extra in py_args and extra not in [
                            p.name for p in gsg_params
                    ]:
                        gsg_params.append(GSGParam(extra, self.libname))
            res.append(GSGMethod(
                method.name, gsg_params, self.libname, static=True
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
        stub += (
            '\nfrom typing import Optional, Any, Tuple, List as PyList\n\n\n'
        )

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

        # global functions
        gsg_functions: List[GSGFunction] = list()
        functions = list(repo.namespace.get_functions())
        for func in functions:
            if not func or not func.name:
                continue
            gsg_functions.append(GSGFunction(
                func.name, [
                    GSGParam(
                        p.name, self.libname,
                        typ=('Optional[Any]' if p.nullable else None),
                        default=('None' if p.optional else None)
                    ) for p in func.parameters if p and p.name
                ], self.libname, self.type_to_pytype(
                    func.return_value.target
                    if func.return_value else None
                )
            ))

        # functions special cases
        if self.libname == 'Gtk':
            for func in gsg_functions:
                if func.name == 'accelerator_parse':
                    func.params = [GSGParam(
                        'accelerator', self.libname, 'str'
                    )]
                    func.ret_typ = 'Tuple[bool, int, Gdk.ModifierType]'
        if self.libname == 'GLib':
            for func in gsg_functions:
                if func.name == 'idle_add':
                    for gsg_param in func.params:
                        if gsg_param.name == 'data':
                            gsg_param.name = '*data'
                            gsg_param.default = None
                    func.params.append(GSGParam(
                        name='priority', module='GLib',
                        typ=(
                            'Literal[PRIORITY_DEFAULT, '
                            'PRIORITY_DEFAULT_IDLE, '
                            'PRIORITY_HIGH, '
                            'PRIORITY_HIGH_IDLE, '
                            'PRIORITY_LOW]'
                        ),
                        default='PRIORITY_DEFAULT'
                    ))

        stub += '\n\n\n'.join([f.to_str() for f in gsg_functions])

        # constants
        constants = [
            GSGField(c.name, c.value).to_str(indent=0)
            for c in repo.namespace.get_constants() if c and c.name
        ]

        stub += '\n\n\n' + '\n'.join(constants)

        stub += '\n\n\n' + self.additional_code
        self.write(stub.strip())


GOBJECT_ADDITIONAL = '''
class Property:
    class __metaclass__(type):
        ...

    def __init__(self, getter=None, setter=None, type=None, default=None,
                 nick='', blurb='', flags=_gi.PARAM_READWRITE,
                 minimum=None, maximum=None):
        ...

    def __get__(self, instance, klass):
        ...

    def __set__(self, instance, value):
        ...

    def __call__(self, fget):
        ...

    def getter(self, fget):
        ...

    def setter(self, fset):
        ...

    def get_pspec_args(self):
        ...
'''

GTK_ADDITIONAL = '''
from typing import Callable as PyCallable


class Template(object):
    def __init__(self,
        string: Optional[str] = None, filename: Optional[str] = None,
        resource_path: Optional[str] = None
    ):
        ...

    def __call__(self, cls):
        ...

    class Callback(object):
        def __init__(self, name: Optional[str] = None):
            ...

        def __call__(self, func: PyCallable):
            ...

    @classmethod
    def Child(cls, name: Optional[str] = None, **kwargs) -> Any:
        ...

    @classmethod
    def from_file(cls, filename: str):
        ...

    @classmethod
    def from_string(cls, string: str):
        ...

    @classmethod
    def from_resource(cls, resource_path: str):
        ...
'''


libs = [
    GirLib('GLib-2.0', 'gi.repository.GLib', []),
    GirLib('GObject-2.0', 'gi.repository.GObject', ['GLib'],
           GOBJECT_ADDITIONAL),
    GirLib('Gio-2.0', 'gi.repository.Gio', ['GObject', 'GLib']),
    GirLib('Pango-1.0', 'gi.repository.Pango', ['GObject']),
    GirLib('Gdk-4.0', 'gi.repository.Gdk', ['Gio', 'GLib', 'GObject']),
    GirLib('GdkPixbuf-2.0', 'gi.repository.GdkPixbuf', [
        'Gdk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('Gtk-4.0', 'gi.repository.Gtk', [
        'Gdk', 'Gio', 'GLib', 'GObject', 'Pango'
    ], GTK_ADDITIONAL),
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
