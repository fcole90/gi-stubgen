#!/usr/bin/env python3

import sys
import os

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(FILE_DIR))

from .templates.gobject_additional import GOBJECT_ADDITIONAL
from .templates.gtk_additional import GTK_ADDITIONAL
from .generators.girlib import GirLib


libs = [
    GirLib('GLib-2.0', 'gi.repository.GLib', []),
    GirLib('GObject-2.0', 'gi.repository.GObject', ['GLib'],
           GOBJECT_ADDITIONAL),
    GirLib('Gdk-3.0', 'gi.repository.Gdk', ['Gio', 'GLib', 'GObject']),
    GirLib('Atk-1.0', 'gi.repository.Atk', ['Gio', 'GLib', 'GObject']),

    GirLib('Gio-2.0', 'gi.repository.Gio', ['GObject', 'GLib']),
    GirLib('Pango-1.0', 'gi.repository.Pango', ['GObject']),
    # GirLib('Gdk-4.0', 'gi.repository.Gdk', ['Gio', 'GLib', 'GObject']),
    GirLib('GdkPixbuf-2.0', 'gi.repository.GdkPixbuf', [
        'Gdk', 'Gio', 'GLib', 'GObject'
    ]),
    GirLib('Gtk-3.0', 'gi.repository.Gtk', [
        'Gdk', 'Gio', 'GLib', 'GObject', 'Pango', 'GdkPixbuf', 'Atk'
    ], GTK_ADDITIONAL),
    # GirLib('Adw-1', 'gi.repository.Adw', [
    #     'Gdk', 'Gtk', 'Gio', 'GLib', 'GObject'
    # ]),
    # GirLib('WebKit2-5.0', 'gi.repository.WebKit2', [
    #     'Gtk', 'Gio', 'GLib', 'GObject'
    # ]),
    # GirLib('GtkSource-5', 'gi.repository.GtkSource', [
    #     'Gtk', 'Gio', 'GLib', 'GObject'
    # ]),
]

if __name__ == '__main__':
    for lib in libs:
        lib.gen()
