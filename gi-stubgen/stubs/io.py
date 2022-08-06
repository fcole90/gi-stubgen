from os import makedirs, path

from ..json_intermediate.types import JSONIntermediateLib
from .generator import generate_lib_stub


def write_stub(data: JSONIntermediateLib, output_dir: str) -> str:
    if not path.isdir(output_dir):
        makedirs(output_dir)
    stub_file_name = data['name'] + '.pyi'
    stub_file_path = path.join(output_dir, stub_file_name)
    with open(path.join(output_dir, stub_file_name), 'w') as fp:
        fp.write(generate_lib_stub(data))
    return stub_file_path
