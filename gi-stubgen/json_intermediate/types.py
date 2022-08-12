from typing import TypedDict, Literal
from gidocgen.gir.ast import Doc, Member
from .utils import infer_type, to_inferred_type


def doc2str(doc: Doc | None) -> str:
    if doc and doc.content:
        return doc.content
    return ""


class LibConstant(TypedDict):
    type: Literal["constant"]
    name: str
    value: str | float | int
    value_type: str
    docstring: str


def make_constant(name: str, value: str, docstring: str = "") -> LibConstant:
    return {
        "type": "constant",
        "name": name,
        "value": to_inferred_type(value),
        "value_type": infer_type(value),
        "docstring": docstring
    }


class LibEnum(TypedDict):
    type: Literal["enum"]
    docstring: str
    name: str
    members: list[LibConstant]


def make_enum(name: str, members: list[Member], docstring: str) -> LibEnum:
    return {
        "type": "enum",
        "name": name,
        "docstring": docstring,
        "members": [
            make_constant(
                name=member.name,
                value=member.value,
            )
            for member in members if member and member.name
        ]
    }


class LibFunctionArg(TypedDict):
    name: str
    type: str
    is_optional: bool


class LibFunction(TypedDict):
    type: Literal["function"]
    docstring: str
    name: str
    args: list[LibFunctionArg]
    return_type: str


def make_function(
    name: str,
    args: list[LibFunctionArg],
    return_type: str,
    docstring: str
) -> LibFunction:
    return {
        "type": "function",
        "name": name,
        "docstring": docstring,
        "args": args,
        "return_type": return_type
    }


class JSONIntermediateLib(TypedDict):
    library: str
    libraryPath: str
    name: str
    version: str
    package: str
    imports: list[str]
    constants: list[LibConstant]
    enums: list[LibEnum]
    functions: list[LibFunction]
    docstring: str
