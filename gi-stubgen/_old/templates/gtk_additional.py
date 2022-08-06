GTK_ADDITIONAL = '''
from typing import Callable as PyCallable


class Template(object):
    def __init__(self,
        string: Optional[str] = None, filename: Optional[str] = None,
        resource_path: Optional[str] = None
    ):
        ...

    def __call__(self, cls):
        ...

    class Callback(object):
        def __init__(self, name: Optional[str] = None):
            ...

        def __call__(self, func: PyCallable):
            ...

    @classmethod
    def Child(cls, name: Optional[str] = None, **kwargs) -> Any:
        ...

    @classmethod
    def from_file(cls, filename: str):
        ...

    @classmethod
    def from_string(cls, string: str):
        ...

    @classmethod
    def from_resource(cls, resource_path: str):
        ...
'''
