#!/usr/bin/env python3

from .json_intermediate.main import generate_intermediate_json
import json

GIR_DIR = '/usr/share/gir-1.0'


def main():
    data = generate_intermediate_json("cairo-1.0", GIR_DIR)
    data_summary = {
        'library': data['library'],
        'libraryPath': data['libraryPath'],
        'name': data['name'],
        'version': data['version'],
        'package': data['package'],
        'docstring': data['docstring'],
        'imports': data['imports'],
    }
    json_summary = json.dumps(data_summary, indent=2)
    print(json_summary)


if __name__ == "__main__":
    main()
