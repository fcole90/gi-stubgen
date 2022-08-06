from typing import Optional


class GSGParam:
    def __init__(
            self,
            name: str,
            module: str,
            typ: Optional[str] = None,
            default: Optional[str] = None,
    ):
        self.name = name.replace('-', '_')
        self.typ = typ
        if self.typ and f'{module}.' in self.typ:
            self.typ = self.typ.removeprefix(f'{module}.')
        self.default = default
        if self.name == '...':
            self.name = '*args'
            self.typ = None
            self.default = None
        elif (
                self.name in (
                    'user_data', 'user_data_free_func', 'user_destroy'
                )
                and self.default is None
        ):
            self.default = 'None'

    def to_str(self) -> str:
        return self.name + (
            f': {self.typ}' if self.typ else ''
        ) + (
            f' = {self.default}' if self.default else ''
        )
