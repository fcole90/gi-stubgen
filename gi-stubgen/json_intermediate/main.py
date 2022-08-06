from gidocgen.gir.ast import Repository
from gidocgen.gir.parser import GirParser

from .types import JSONIntermediateLib, LibConstant, LibEnum, make_constant, make_enum, doc2str

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


def generate_intermediate_json(library: str,  library_path: str, package: str = "gi.repository") -> JSONIntermediateLib:
    name, version = library.split('-')
    gir_lib_path = f'{library_path}/{library}.gir'

    print(f"Loading parser for {library}...", end=" ")
    repo: Repository = _load_gir_parser(gir_lib_path)
    print("Done")

    library_constants = _get_constants(repo)
    library_enums = _get_enums(repo)
    library_imports = [
        package
        for lib in repo.includes
        for package in repo.includes[lib].packages
        if len(repo.includes[lib].packages) > 0
    ]

    data: JSONIntermediateLib = {
        'library': library,
        'libraryPath': gir_lib_path,
        'name': name,
        'version': version,
        'package': package,
        'docstring': '',
        'imports': library_imports,
        'constants': library_constants,
        'enums': library_enums
    }

    return data
