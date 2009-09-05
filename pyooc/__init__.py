import ctypes
import ctypes.util
from functools import partial

class BindingError(Exception):
    pass

# Hey, we've got to load libgc!
GC = ctypes.CDLL(ctypes.util.find_library('gc'), ctypes.RTLD_GLOBAL)

class Library(ctypes.CDLL):
    pass

class KindOfClass(ctypes.c_void_p):
    name = None
    _library = None
    fields = None
    _struct = None

    @classmethod
    def bind(cls, lib):
        cls._library = lib

    @classmethod
    def _setup(cls):
        if cls.name is None:
            cls.name = cls.__name__
        struct = type(cls.__name__ + 'Struct', (ctypes.Structure,), {})
        if cls.fields is None:
            cls.fields = []
        # TODO: bitfields??
        fields = struct._fields_ = [
                ('class_', ctypes.POINTER(None)) # TODO: well, include the _Object struct
                ]
        fields.extend(cls.fields)
#        struct._anonymous_ = ('__super__',)
        cls._struct = struct

    @classmethod
    def setup(cls):
        if cls._struct is None:
            self._setup()

    @classmethod
    def _get_name(cls, name):
        basename = cls.name
        if basename is None:
            basename = cls.__name__
        return '_'.join((basename, name))

    @classmethod
    def method(cls, name, restype=None, argtypes=None):
        if cls._library is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._library[name]
        func.argtypes = [ctypes.POINTER(cls._struct)]
        if restype is not None:
            func.restype = restype
        if argtypes is not None:
            func.argtypes.extend(argtypes)
        return func

    @classmethod
    def static_method(cls, name, restype=None, argtypes=None):
        if cls._library is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._library[name]
        if restype is not None:
            func.restype = restype
        if argtypes is not None:
            func.argtypes = argtypes
        return func

    @classmethod
    def constructor(cls, suffix='', argtypes=None):
        """
            a constructor is a static method `new` that
            returns a pointer to *cls._struct*.
        """
        if suffix:
            name = 'new_' + suffix
        else:
            name = 'new'
        return cls.static_method(name, cls, argtypes)

    @classmethod
    def add_method(cls, name, *args, **kwargs):
        ctypes_meth = cls.method(name, *args, **kwargs)
        def method(self, *args, **kwargs):
            return ctypes_meth(self, *args, **kwargs)
        setattr(cls, name, method)

    @classmethod
    def add_static_method(cls, name, *args, **kwargs):
        ctypes_meth = cls.static_method(name, *args, **kwargs)
        setattr(cls, name, staticmethod(ctypes_meth))

    @classmethod
    def add_constructor(cls, suffix='', argtypes=None):
        ctypes_meth = cls.constructor(suffix, argtypes)
        if suffix:
            name = 'new_' + suffix
        else:
            name = 'new'
        setattr(cls, name, staticmethod(ctypes_meth)) # TODO: overloaded?

class Class(KindOfClass):
    pass

