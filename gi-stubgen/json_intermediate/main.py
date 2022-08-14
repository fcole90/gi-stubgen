
from gidocgen.gir.ast import Repository, Type
from gidocgen.gir.parser import GirParser

from .types import JSONIntermediateLib, LibConstant, LibEnum, LibFunction, make_constant, make_enum, make_function, doc2str
from .aliased_types import is_aliased_type, get_aliased_matching_type


GIR_DIR = '/usr/share/gir-1.0'
OUTPUT_DIR = '.intermediate'


def _load_gir_parser(library_path: str) -> Repository:
    parser = GirParser([GIR_DIR])
    parser.parse(library_path)
    repo = parser.get_repository()
    assert(repo is not None and repo.namespace is not None)
    return repo


def _get_type_str(t: Type | None) -> str:
    if t is None or t.name is None:
        # We can't infer the type, so we return the most generic type
        return 'object'

    if is_aliased_type(t.name):
        return get_aliased_matching_type(t.name)

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


def _get_functions(repo: Repository) -> list[LibFunction]:
    if repo.namespace is None:
        return []

    return [
        make_function(
            name=fun.name,
            args=[
                {
                    'name': arg.name,
                    'type': _get_type_str(arg.target),
                    'is_optional': arg.optional,
                    'is_nullable': arg.nullable
                }
                for arg in fun.parameters
                if arg.name is not None
            ],
            return_type=_get_type_str(
                fun.return_value.target) if fun.return_value is not None else _get_type_str(None),
            docstring=doc2str(fun.doc)
        )
        for fun in list(repo.namespace.get_functions())
        if fun.name is not None
    ]


def generate_intermediate_json(library: str,  library_path: str, package: str = 'gi.repository') -> JSONIntermediateLib:
    name, version = library.split('-')
    gir_lib_path = f'{library_path}/{library}.gir'

    print(f'Loading parser for {library}...', end=' ')
    repo: Repository = _load_gir_parser(gir_lib_path)
    print('Done')

    library_constants = _get_constants(repo)
    library_enums = _get_enums(repo)
    library_functions = _get_functions(repo)
    library_imports = list(repo.includes.keys())

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

    data: JSONIntermediateLib = {
        'library': library,
        'libraryPath': gir_lib_path,
        'name': name,
        'version': version,
        'package': package,
        'docstring': '',
        'imports': library_imports,
        'constants': library_constants,
        'functions': library_functions,
        'enums': library_enums
    }

    return data
