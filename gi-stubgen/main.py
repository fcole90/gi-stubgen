#!/usr/bin/env python3
from os import path
from typing import Mapping, List
from .json_intermediate.main import generate_intermediate_json
from .json_intermediate import writer
from .utils import get_files


OUTPUT_DIR = '.intermediate'
GIR_DIR = '/usr/share/gir-1.0'


def main():
    missing_libs: List[str] = list()
    gir_mapping = get_gir_mappings(GIR_DIR)
    generation_loop("Gtk-3.0", gir_mapping, missing_libs)

    print("Generation completed!")
    if len(missing_libs) > 0:
        print("Could not find girs for:", missing_libs)


def get_gir_mappings(library_path: str) -> Mapping[str, str]:
    gir_files = get_files(library_path)
    low_case_names = [
        '.'.join(gir.split('.')[:-1]).lower()
        for gir in gir_files
    ]

    low_case_names_no_version = [
        '-'.join(name.split('-')[:-1]).lower()
        for name in low_case_names
    ]

    return {
        name: '.'.join(gir.split('.')[:-1])
        for name, gir in zip(low_case_names + low_case_names_no_version, gir_files + gir_files)
    }


def generation_loop(lib: str, gir_mapping: Mapping[str, str], missing_libs: List[str]):
    data = generate_intermediate_json(lib, GIR_DIR)
    json_file_path = writer.write_json(data, OUTPUT_DIR)
    print(f"Generated {json_file_path}\n")

    print("Retrieving deps for " + lib)
    for dep_lib in data["imports"]:
        if dep_lib in gir_mapping.keys():
            gir = gir_mapping[dep_lib]
            gir_intermediate_file = gir + ".json"
            if not path.exists(path.join(OUTPUT_DIR, gir_intermediate_file)):
                print(
                    f"- Generating intermediates for {gir_intermediate_file}...")
                generation_loop(gir, gir_mapping, missing_libs)
            else:
                print(f"- {gir_intermediate_file} already exists. Skipping...")

        else:
            print("- Could not find " + dep_lib)
            if dep_lib not in missing_libs:
                missing_libs.append(dep_lib)


if __name__ == '__main__':
    main()
