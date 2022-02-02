#!/usr/bin/env python3

from os import makedirs
from typing import List
from gidocgen.gir.ast import Class
from gidocgen.gir.parser import GirParser
from os.path import isdir


GIR_DIR = '/usr/share/gir-1.0'


class GirLib:
    def __init__(self, girname: str, package: str, imports: List[str] = []):
        # IE: 'Gtk-4.0'
        self.girname = girname
        self.girpath = f'{GIR_DIR}/{self.girname}.gir'
        # IE: 'gi.repository.Gtk'
        self.package = package
        # IE: ['Gdk', 'Gio', 'GLib']
        self.imports = imports

        self.dest_dir = './out/' + '/'.join(self.package.split('.')[:-1])
        self.dest = f'{self.dest_dir}/{self.package.split(".")[-1]}.pyi'

    def write(self, stub: str):
        if not isdir(self.dest_dir):
            makedirs(self.dest_dir)
        with open(self.dest, 'w') as fd:
            fd.write(stub)

    def gen(self):
        parser = GirParser([GIR_DIR])
        parser.parse(self.girpath)
        repo = parser.get_repository()
        assert(repo is not None and repo.namespace is not None)

        stub = ''
        if len(self.imports) > 0:
            stub += 'from gi.repository import ' + ', '.join(self.imports)
            stub += '\n\n\n'

        # classes
        for cls in repo.namespace.get_classes():
            if not cls.name:
                continue
            stub += 'class '
            # for multiple inheritance
            # stub += cls.name + '(' + ', '.join([anc.name for anc in cls.ancestors]) + ')'
            stub += cls.name
            if len(cls.ancestors) > 0:
                ancestor = cls.ancestors[0]
                assert(isinstance(ancestor, Class))
                stub += ((
                    '(' + (ancestor.name or 'Object') + ')'
                ) if ancestor is not None else '') + ':\n'
                stub += '    def __init__(self, ' + ', '.join(
                    [
                        prop.replace('-', '_') + '=None'
                        for prop in cls.properties.keys()
                    ] +
                    [
                        prop.replace('-', '_') + '=None'
                        for prop in (
                            ancestor.properties.keys() if ancestor else []
                        )
                    ]
                ) + '):\n'
            else:
                stub += ':\n'
                stub += '    def __init__(self,' + ', '.join([
                    prop.replace('-', '_') + '=None'
                    for prop in cls.properties.keys()
                ]) + '):\n'
            stub += '        ...\n\n'
            for method in cls.methods:
                if not method or not method.name:
                    continue
                stub += '    def ' + method.name + '(self, ' + ', '.join([
                    ('*args' if param.name == '...' else param.name)
                    for param in method.parameters if param.name
                ]) + '):\n'
                stub += '        ...\n\n'
            stub += '\n\n'

        # enums
        enums = list(repo.namespace.get_enumerations())
        enums.extend(repo.namespace.get_bitfields())
        for enum in enums:
            if not enum or not enum.name:
                continue
            stub += 'class ' + enum.name + ':\n'
            for member in enum.members:
                stub += f'    {member.name.upper()} = {member.value}\n'
            stub += '\n\n'

        self.write(stub)


libs = [
    GirLib('GObject-2.0', 'gi.repository.GObject', []),
    GirLib('GLib-2.0', 'gi.repository.GLib', ['GObject']),
    GirLib('Gio-2.0', 'gi.repository.Gio', ['GObject']),
    GirLib('Gdk-4.0', 'gi.repository.Gdk', ['Gio', 'GLib', 'GObject']),
    GirLib('GdkPixbuf-2.0', 'gi.repository.GdkPixbuf', [
        'Gdk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('Gtk-4.0', 'gi.repository.Gtk', ['Gdk', 'Gio', 'GLib', 'GObject']),
    GirLib('Adw-1', 'gi.repository.Adw', [
        'Gdk', 'Gtk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('WebKit2-5.0', 'gi.repository.WebKit2', [
        'Gtk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('GtkSource-5', 'gi.repository.GtkSource', [
        'Gtk', 'Gio', 'GLib', 'GObject'
    ]),
]
for lib in libs:
    lib.gen()
