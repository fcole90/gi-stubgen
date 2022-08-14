#!/usr/bin/env python3
from os import path
from .json_intermediate.io import read_json
from .stubs.io import write_stub
from .utils import get_files


INPUT_DIR = '.intermediate'
OUTPUT_DIR = '.stubs'


def main():
    json_intermediate_files = get_files(INPUT_DIR)

    for json_file in json_intermediate_files:
        lib_data = read_json(path.join(INPUT_DIR, json_file))
        write_stub(lib_data, path.join(
            OUTPUT_DIR, lib_data['package'].replace('.', path.sep)))


if __name__ == '__main__':
    main()
