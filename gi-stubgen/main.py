#!/usr/bin/env python3
from os import path
from typing import Optional
from .json_intermediate.main import generate_intermediate_json
from .json_intermediate.io import write_json
from .utils import get_gir_mappings


OUTPUT_DIR = '.intermediate'
DEFAULT_GIR_DIR = '/usr/share/gir-1.0'


def main():
    missing_libs: list[str] = list()
    # gir_mapping = get_gir_mappings(DEFAULT_GIR_DIR)
    generation_loop('Gtk-3.0')

    print('Generation completed!')
    if len(missing_libs) > 0:
        print('Could not find girs for:', missing_libs)


def generation_loop(lib: str, gir_dir: str = '', missing_libs: Optional[list[str]] = None):
    if missing_libs is None:
        missing_libs = []

    data = generate_intermediate_json(
        lib, gir_dir if gir_dir else DEFAULT_GIR_DIR)
    json_file_path = write_json(data, OUTPUT_DIR)
    print(f'Generated {json_file_path}\n')

    print('Retrieving deps for ' + lib)
    for dep_gir_path in data['import_girs']:
        if path.exists(dep_gir_path):
            dep_name, dep_gir_dir = '', ''
            if path.sep in dep_gir_path:
                dep_gir_dir = path.sep.join(dep_gir_path.split(path.sep)[:-1])
                dep_gir_file_name = dep_gir_path.split(path.sep)[-1]
                dep_name = '.'.join(dep_gir_file_name.split('.')[:-1])

            gir_intermediate_file = dep_name + '.json'
            if not path.exists(path.join(OUTPUT_DIR, gir_intermediate_file)):
                print(
                    f'- Generating intermediates for {gir_intermediate_file}...')
                generation_loop(dep_name, dep_gir_dir, missing_libs)
            else:
                print(f'- {gir_intermediate_file} already exists. Skipping...')

        else:
            print('- Could not find ' + dep_gir_path)
            if dep_gir_path not in missing_libs:
                missing_libs.append(dep_gir_path)


if __name__ == '__main__':
    main()
