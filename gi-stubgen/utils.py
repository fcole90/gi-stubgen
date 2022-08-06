from typing import List

from os import listdir
from os.path import isfile, join


def get_files(library_path: str) -> List[str]:
    only_files = [file for file in listdir(
        library_path) if isfile(join(library_path, file))]
    return only_files
