import importlib
import inspect
from os import makedirs, path
from typing import List, Optional, Union as TUnion
from gidocgen.gir.ast import (
    ArrayType, Class, GIRElement, Interface, ListType, Type, Union, Record
)
from gidocgen.gir.parser import GirParser
from os.path import isdir
import gi

from ..types.type_map import TYPE_MAP
from .gsgfield import GSGField
from .gsgparam import GSGParam
from .gsgfunction import GSGFunction
from .gsgmethod import GSGMethod
from .gsgclass import GSGClass


GIR_DIR = '/usr/share/gir-1.0'
OUTPUT_DIR = '.out'
TYPE_UNKNOWN = '-99999'
LEN_NAME_FRAGMENTS = [
    'n_', 'num_', 'size', 'len'
]


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

        self.dest_dir = path.join(".", OUTPUT_DIR, *self.package.split('.')[:-1])
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