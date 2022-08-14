__ALIASED_TYPES_MAP__ = {
    # GLib Basic Types: https://developer.gimp.org/api/2.0/glib/glib-Basic-Types.html
    'gboolean':      'bool',

    'gpointer':      'object',
    'gconstpointer': 'object',

    'gchar':         'str',
    'guchar':        'str',

    'gint':          'int',
    'guint':         'int',
    'gshort':        'int',
    'gushort':       'int',
    'glong':         'int',
    'gulong':        'int',
    'gint8':         'int',
    'guint8':        'int',
    'gint16':        'int',
    'guint16':       'int',
    'gint32':        'int',
    'guint32':       'int',

    'gfloat':        'float',
    'gdouble':       'float',

    'gsize':         'int',
    'gssize':        'int',
    'goffset':       'int',

    # GLib Unicode: https://www.freedesktop.org/software/gstreamer-sdk/data/docs/2012.5/glib/glib-Unicode-Manipulation.html
    'gunichar':      'str',
    'gunichar2':     'str',

    # Misc
    'none':          'None',
    'boolean':       'bool',
    'pointer':       'object',
    'char':          'str',
    'utf8':          'str',
    'filename':      'str',
    'long':          'int',
    'double':        'float',
    'va_list':       'list'
}


def is_aliased_type(t: str) -> bool:
    return t in __ALIASED_TYPES_MAP__


def get_aliased_matching_type(t: str) -> str:
    return __ALIASED_TYPES_MAP__[t]
