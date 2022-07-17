from typing import Optional, List
from .gsgparam import GSGParam


class GSGFunction:
    def __init__(
        self, name: str, params: List[GSGParam], module: str,
        ret_typ: Optional[str] = None
    ):
        self.name = name + ('_' if name in (
            'continue', 'yield'
        ) else '')
        self.params = params
        self.ret_typ = ret_typ
        if self.ret_typ and f'{module}.' in self.ret_typ:
            self.ret_typ = self.ret_typ.removeprefix(f'{module}.')

    def to_str(self, indent: int = 0) -> str:
        return (indent * '    ') + (
            f'def {self.name}('
        ) + ', '.join([p.to_str() for p in self.params]) + ')' + (
            f' -> {self.ret_typ}' if self.ret_typ else ''
        ) + ':\n' + ((indent+1) * '    ') + '...'
