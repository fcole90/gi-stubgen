GOBJECT_ADDITIONAL = '''
class Property:
    class __metaclass__(type):
        ...

    def __init__(self, getter=None, setter=None, type=None, default=None,
                 nick='', blurb='', flags=_gi.PARAM_READWRITE,
                 minimum=None, maximum=None):
        ...

    def __get__(self, instance, klass):
        ...

    def __set__(self, instance, value):
        ...

    def __call__(self, fget):
        ...

    def getter(self, fget):
        ...

    def setter(self, fset):
        ...

    def get_pspec_args(self):
        ...
'''
