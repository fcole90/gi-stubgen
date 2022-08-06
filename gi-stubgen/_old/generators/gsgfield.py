from typing import Optional


class GSGField:
    def __init__(
            self, name: str, value: str = '...', typ: Optional[str] = None
    ):
        self.name = name
        self.value = value
        self.typ = typ
    
    def py_value(self) -> str:
        if self.value == "true":
            return "True"
        elif self.value == "false":
            return "False"
        elif self.value.isnumeric():
            return self.value
        else:
            return f'"{self.value}"'


    def to_str(self, indent: int = 1) -> str:
        return (indent * '    ') + '{0}{1} = {2}'.format(
            self.name,
            f': {self.typ}' if self.typ else '',
            self.py_value()
        )
