from jinja2 import Environment, PackageLoader

from ..json_intermediate.types import JSONIntermediateLib

PKG_NAME = "gi-stubgen"

environment = Environment(loader=PackageLoader(
    f"{PKG_NAME}.stubs", "templates")
)


def generate_lib_stub(data: JSONIntermediateLib):
    return environment.get_template("lib.py.jinja").render(
        lib_name=data["name"],
        gen_name=PKG_NAME,
        constants=data["constants"][:5],
        enums=data["enums"][:1],
        imports=[{
            "from": "enum",
            "imports": ["Enum"]
        }]
    ) + "\n"
