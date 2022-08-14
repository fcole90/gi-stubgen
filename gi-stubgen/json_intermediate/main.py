
from gidocgen.gir.ast import Repository, Type, Parameter
from gidocgen.gir.parser import GirParser

from .types import JSONIntermediateLib, LibConstant, LibEnum, LibFunction, LibClass, LibFunctionArg, make_constant, make_enum, make_function, make_class, doc2str
from .aliased_types import is_aliased_type, get_aliased_matching_type


GIR_DIR = '/usr/share/gir-1.0'
OUTPUT_DIR = '.intermediate'


def _load_gir_parser(library_path: str) -> Repository:
    parser = GirParser([GIR_DIR])
    parser.parse(library_path)
    repo = parser.get_repository()
    assert(repo is not None and repo.namespace is not None)
    return repo


def _get_type_str(t: Type | None, lib_name: str) -> str:
    if t is None or t.name is None or t.name == 'None':
        # We can't infer the type, so we return the most generic type
        return 'object'

    if is_aliased_type(t.name):
        at = get_aliased_matching_type(t.name)
        if at == 'None':
            return 'object'
        return at

    if t.name.startswith(f"{lib_name}."):
        # E.g. Gtk.Window => Window
        return '.'.join(t.name.split('.')[1:])

    return t.name


def _get_constants(repo: Repository) -> list[LibConstant]:
    if repo.namespace is None:
        return []

    return [
        make_constant(
            name=constant.name,
            value=constant.value,
            docstring=doc2str(constant.doc)
        )
        for constant in repo.namespace.get_constants()
        if constant and constant.name and constant.value
    ]


def _get_enums(repo: Repository) -> list[LibEnum]:
    if repo.namespace is None:
        return []

    return [
        make_enum(
            name=enum.name,
            members=enum.members,
            docstring=doc2str(enum.doc)
        )
        for enum in repo.namespace.get_enumerations()
        if enum and enum.name and enum.members
    ] + [
        make_enum(
            name=enum.name,
            members=enum.members,
            docstring=doc2str(enum.doc)
        )
        for enum in repo.namespace.get_bitfields()
        if enum and enum.name and enum.members
    ]


def _prepare_arg(arg: Parameter, lib_name: str) -> LibFunctionArg:
    if arg.name == '...':
        return {
            'name': '*args',
            'type': _get_type_str(arg.target, lib_name),
            'is_optional': False,
            'is_nullable': False
        }

    return {
        'name': arg.name if arg.name else 'MISSING_NAME',
        'type': _get_type_str(arg.target, lib_name),
        'is_optional': arg.optional,
        'is_nullable': arg.nullable
    }


def _get_functions(repo: Repository, lib_name: str) -> list[LibFunction]:
    if repo.namespace is None:
        return []

    return [
        make_function(
            name=fun.name,
            args=[
                _prepare_arg(arg, lib_name)
                for arg in fun.parameters
                if arg.name is not None
            ],
            return_type=_get_type_str(fun.return_value.target, lib_name)
            if fun.return_value is not None
            else _get_type_str(None, lib_name),
            docstring=doc2str(fun.doc)
        )
        for fun in list(repo.namespace.get_functions())
        if fun.name is not None
    ]


def _get_classes(repo: Repository, lib_name: str) -> list[LibClass]:
    if repo.namespace is None:
        return []

    self_arg: LibFunctionArg = {
        'name': 'self',
        'type': '',
        'is_optional': False,
        'is_nullable': False
    }

    cls_arg: LibFunctionArg = {
        'name': 'cls',
        'type': '',
        'is_optional': False,
        'is_nullable': False
    }

    return [
        make_class(
            name=cls.name,
            docstring=doc2str(cls.doc),
            is_abstract=cls.abstract,
            inherited_classes=[
                _get_type_str(cls.parent, lib_name)
            ] + [
                _get_type_str(im, lib_name)
                for im in cls.implements
            ],
            constructors=[
                # __init__
                make_function(
                    name='__init__',
                    args=[self_arg] + [
                        {
                            'name': '*args',
                            'type': 'object',
                            'is_optional': False,
                            'is_nullable': False
                        }, {
                            'name': '**kwargs',
                            'type': 'object',
                            'is_optional': False,
                            'is_nullable': False
                        }
                    ],
                    return_type='None',
                    docstring=''
                )
            ] + [
                # Other constructors
                make_function(
                    name=c.name,
                    args=[cls_arg] + [
                        _prepare_arg(arg, lib_name)
                        for arg in c.parameters
                        if arg.name is not None
                    ],
                    return_type=_get_type_str(c.return_value.target, lib_name)
                    if c.return_value is not None
                    else f"'{cls.name}'",
                    docstring=doc2str(c.doc)
                ) for c in cls.constructors
                if c.name is not None
            ],
            methods=[
                make_function(
                    name=m.name,
                    args=[self_arg] + [
                        _prepare_arg(arg, lib_name)
                        for arg in m.parameters
                        if arg.name is not None
                    ],
                    return_type=_get_type_str(m.return_value.target, lib_name)
                    if m.return_value is not None
                    else _get_type_str(None, lib_name),
                    docstring=doc2str(m.doc)
                ) for m in cls.methods
                if m.name is not None
            ]
        ) for cls in list(repo.namespace.get_classes())
        if cls.name is not None
    ]


def generate_intermediate_json(library: str,  library_path: str, package: str = 'gi.repository') -> JSONIntermediateLib:
    name, version = library.split('-')
    gir_lib_path = f'{library_path}/{library}.gir'

    print(f'Loading parser for {library}...', end=' ')
    repo: Repository = _load_gir_parser(gir_lib_path)
    print('Done')

    library_constants = _get_constants(repo)
    library_enums = _get_enums(repo)
    library_functions = _get_functions(repo, name)
    library_classes = _get_classes(repo, name)
    library_imports = list(repo.includes.keys())
    library_import_girs = [
        lib.girfile if lib.girfile is not None else ''
        for lib in repo.includes.values()
    ]
    # print(repo.girfile)
    # print(repo.packages)

    # print('\nAlias:', repo.namespace.get_aliases())
    # print('\nBoxeds:', repo.namespace.get_boxeds())
    # print('\nBitfields:', repo.namespace.get_bitfields())
    # print('\nEffective Records:', repo.namespace.get_effective_records())
    # print('\nUnions:', repo.namespace.get_unions())
    # print('\nGuint:', repo.namespace.find_real_type('guint'))
    # if repo.namespace is not None:
    #     funs = repo.namespace.get_functions()
    #     function_names = [fun.name for fun in funs]
    #     function_param0 = [{
    #         'nullable': fun.parameters[0].nullable,
    #         'optional': fun.parameters[0].optional,
    #     } if len(fun.parameters) > 0 else {}
    #         for fun in funs]
    #     function_returns = [fun.return_value.target for fun in funs]
    #     for fn, fr, fp0 in zip(function_names, function_returns, function_param0):
    #         print(fn, fr, 'CType:', fr.ctype, "Param0:", fp0)
    # exit()

    # print('---')
    # print(repo.includes)
    # print(repo.includes[list(repo.includes.keys())[0]].types)
    # print(repo.includes[list(repo.includes.keys())[0]].includes)
    # print(repo.includes[list(repo.includes.keys())[0]].girfile)
    # print('---')

    # c = list(repo.namespace.get_classes())[5]
    # print(c.constructors)
    # print(c.constructors[0].info)
    # print(c.constructors[0].name)
    # print([(p.name, p.target.name)
    #       for p in list(c.constructors[0].parameters)])

    # print()

    # for mtd in c.methods:
    #     print(mtd.name)
    #     print([(p.name, p.target.name)
    #            for p in list(mtd.parameters)])

    # exit()

    # print(list(repo.namespace.get_classes())[0].name)
    # print(list(repo.namespace.get_classes())[0].implements)
    # print(list(repo.namespace.get_classes())[0].parent)
    # exit()

    data: JSONIntermediateLib = {
        'library': library,
        'libraryPath': gir_lib_path,
        'name': name,
        'version': version,
        'package': package,
        'imports': library_imports,
        'import_girs': library_import_girs,
        'docstring': '',

        'constants': library_constants,
        'functions': library_functions,
        'classes': library_classes,
        'enums': library_enums
    }

    return data
