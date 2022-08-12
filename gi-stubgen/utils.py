from typing import Mapping, List
from os import listdir
from os.path import isfile, join


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


def get_files(library_path: str) -> List[str]:
    only_files = [file for file in listdir(
        library_path) if isfile(join(library_path, file))]
    return only_files
