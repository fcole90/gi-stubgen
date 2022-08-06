from typing import List

from .gsgfield import GSGField
from .gsgparam import GSGParam
from .gsgmethod import GSGMethod


class GSGClass:
    def __init__(
        self,
        name: str,
        methods: List[GSGMethod],
        module: str,
        ancestors: List[str] = [],
        fields: List[GSGField] = [],
        docstring: str = "",
    ):
        self.name = name
        self.methods = methods
        self.module = module
        self.ancestors = [
            anc.removeprefix(f'{module}.') if f'{module}.' in anc else anc
            for anc in ancestors
        ]
        self.fields = fields
        self.manage_special_cases()
        self.docstring = docstring

    def to_str(self, indent: int = 0) -> str:
        res = (indent * '    ') + f'class {self.name}' + (
            f'({", ".join(self.ancestors)})'
            if len(self.ancestors) > 0 else ''
        ) + ':\n'
        if len(self.docstring) > 0:
            res += ((indent+1) * '    ') + '"""' + "\n"
            for line in self.docstring.split("\n"):
                res += ((indent+1) * '    ') + line + "\n"
            res += ((indent+1) * '    ') + '"""' + "\n"
        if len(self.methods) <= 0 and len(self.fields) <= 0:
            res += ((indent+1) * '    ') + '...'
            return res
        res += '\n'.join([f.to_str(indent+1) for f in self.fields])
        res += (
            '\n\n' if len(self.fields) > 0 else ''
        ) + '\n\n'.join(
            [m.to_str(indent+1) for m in self.methods]
        )
        return res

    def manage_special_cases(self):
        if self.module == 'GLib':
            if self.name == 'Hook':
                self.methods = [
                    m for m in self.methods
                    if m.name != 'destroy'
                ]
            elif self.name == 'MainContext':
                self.methods = [
                    m for m in self.methods
                    if m.name != 'get_poll_func'
                ]
        elif self.module == 'Gio':
            if self.name == 'ListModel':
                self.methods += [
                    GSGMethod('__iter__', [], self.module),
                    GSGMethod(
                        '__getitem__',
                        [GSGParam(name='i', typ='int', module=self.module)],
                        self.module,
                        ret_typ='Any'
                    ),
                    GSGMethod('__len__', [], self.module),
                ]
        elif self.module == 'GObject':
            if self.name == 'Object':
                self.methods += [GSGMethod('emit', [
                    GSGParam('signal', self.module, 'str'),
                    GSGParam('*args', self.module)
                ], self.module)]
        elif self.module == 'Gdk':
            if self.name == 'Paintable':
                compute_concrete_size = [
                    m for m in self.methods
                    if m.name == 'compute_concrete_size'
                ][0]
                self.methods = [
                    m for m in self.methods
                    if m.name != 'compute_concrete_size'
                ]
                compute_concrete_size.params = [
                    p for p in compute_concrete_size.params
                    if p.name not in (
                        'concrete_width', 'concrete_height'
                    )
                ]
                compute_concrete_size.ret_typ = 'Tuple[float, float]'
                self.methods.append(compute_concrete_size)
