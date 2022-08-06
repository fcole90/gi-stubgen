from os import makedirs, path

import json


from .types import JSONIntermediateLib


def write_json(data: JSONIntermediateLib, output_dir: str) -> str:
    if not path.isdir(output_dir):
        makedirs(output_dir)
    json_file_name = data['library'] + '.json'
    json_file_path = path.join(output_dir, json_file_name)
    with open(path.join(output_dir, json_file_name), 'w') as fp:
        json.dump(data, fp, indent=2)
    return json_file_path
