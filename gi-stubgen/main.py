#!/usr/bin/env python3
# from .generators.girlib import GirLib
# from .templates.gobject_additional import GOBJECT_ADDITIONAL
# from .templates.gtk_additional import GTK_ADDITIONAL
from .json_intermediate import main

# libs = [
#     GirLib('cairo-1.0', 'gi.repository.cairo', []),
#     GirLib('Atk-1.0', 'gi.repository.Atk', []),
#     GirLib('GLib-2.0', 'gi.repository.GLib', []),
#     GirLib('GObject-2.0', 'gi.repository.GObject', ['GLib'], GOBJECT_ADDITIONAL),
#     GirLib('Pango-1.0', 'gi.repository.Pango', ['GObject']),
#     GirLib('GdkPixbuf-2.0', 'gi.repository.GdkPixbuf', []),
#     GirLib('Gio-2.0', 'gi.repository.Gio', ['GObject', 'GLib']),
#     GirLib('Gdk-3.0', 'gi.repository.Gdk', ['cairo', 'GdkPixbuf', 'Gio', 'GLib', 'GObject']),
#     GirLib('Gtk-3.0', 'gi.repository.Gtk', ['Gdk', 'Gio', 'GLib', 'GObject', 'Pango', 'GdkPixbuf', 'Atk'], GTK_ADDITIONAL),
#     GirLib('WebKit2-4.1', 'gi.repository.WebKit2'),
    

    
    
    # GirLib('Gdk-4.0', 'gi.repository.Gdk', ['Gio', 'GLib', 'GObject']),
    
    


    # GirLib('Adw-1', 'gi.repository.Adw', [
    #     'Gdk', 'Gtk', 'Gio', 'GLib', 'GObject'
    # ]),
    # GirLib('WebKit2-5.0', 'gi.repository.WebKit2', [
    #     'Gtk', 'Gio', 'GLib', 'GObject'
    # ]),
    # GirLib('GtkSource-5', 'gi.repository.GtkSource', [
    #     'Gtk', 'Gio', 'GLib', 'GObject'
    # ]),
# ]

if __name__ == '__main__':
    main.generate_intermediate_json("Gtk-3.0")
