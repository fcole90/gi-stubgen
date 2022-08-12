
from gidocgen.gir.ast import Repository
from gidocgen.gir.parser import GirParser

from .types import JSONIntermediateLib, LibConstant, LibEnum, LibFunction, make_constant, make_enum, make_function, doc2str

GIR_DIR = '/usr/share/gir-1.0'
OUTPUT_DIR = '.intermediate'


def _load_gir_parser(library_path: str) -> Repository:
    parser = GirParser([GIR_DIR])
    parser.parse(library_path)
    repo = parser.get_repository()
    assert(repo is not None and repo.namespace is not None)
    return repo


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
                    "name": arg.name,
                    "type": arg.target.name if arg.target.name is not None else "Unknown",
                    "is_optional": arg.optional
                }
                for arg in fun.parameters
                if arg.name is not None
            ],
            return_type=fun.return_value.target.name if fun.return_value is not None and fun.return_value.target.name is not None else "None",
            docstring=doc2str(fun.doc)
        )
        for fun in list(repo.namespace.get_functions())
        if fun.name is not None
    ]


def generate_intermediate_json(library: str,  library_path: str, package: str = "gi.repository") -> JSONIntermediateLib:
    name, version = library.split('-')
    gir_lib_path = f'{library_path}/{library}.gir'

    print(f"Loading parser for {library}...", end=" ")
    repo: Repository = _load_gir_parser(gir_lib_path)
    print("Done")

    library_constants = _get_constants(repo)
    library_enums = _get_enums(repo)
    library_functions = _get_functions(repo)
    library_imports = list(repo.includes.keys())

    # print("---")
    # print(repo.includes)
    # print(repo.includes[list(repo.includes.keys())[0]].types)
    # print(repo.includes[list(repo.includes.keys())[0]].includes)
    # print(repo.includes[list(repo.includes.keys())[0]].girfile)
    # print("---")

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
