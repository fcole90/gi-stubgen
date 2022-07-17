
from typing import List, Optional

from .gsgfunction import GSGFunction
from .gsgparam import GSGParam


class GSGMethod(GSGFunction):
    def __init__(
            self, name: str, params: List[GSGParam], module: str,
            ret_typ: Optional[str] = None, static: bool = False
    ):
        self.static = static
        params.insert(0, GSGParam(
            'cls' if self.static else 'self', module
        ))
        super().__init__(name, params, module, ret_typ)

    def to_str(self, indent: int = 1) -> str:
        return (
            ((indent * '    ') + '@classmethod\n') if self.static else ''
        ) + super().to_str(indent)
