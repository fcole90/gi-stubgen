from typing import Optional


class GSGField:
    def __init__(
            self, name: str, value: str = '...', typ: Optional[str] = None
    ):
        self.name = name
        self.value = value
        self.typ = typ

    def to_str(self, indent: int = 1) -> str:
        return (indent * '    ') + '{0}{1} = {2}'.format(
            self.name,
            f': {self.typ}' if self.typ else '',
            self.value
        )
