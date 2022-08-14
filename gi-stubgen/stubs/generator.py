from jinja2 import Environment, PackageLoader

from ..json_intermediate.types import JSONIntermediateLib

PKG_NAME = 'gi-stubgen'

environment = Environment(loader=PackageLoader(
    f'{PKG_NAME}.stubs', 'templates')
)


def generate_lib_stub(data: JSONIntermediateLib):
    return environment.get_template('lib.py.jinja').render(
        lib_name=data['name'],
        gen_name=PKG_NAME,
        constants=data['constants'],
        enums=data['enums'],
        functions=data['functions'],
        classes=data['classes'],
        imports=[{
            'from': 'enum',
            'imports': ['Enum']
        }] + [{
            'from': 'gi.repository',
            'imports': data['imports']
        }]
    ) + '\n'
