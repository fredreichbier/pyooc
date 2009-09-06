import ctypes
import ctypes.util
from functools import partial

from . import types

class BindingError(Exception):
    pass

OPERATORS = {
        '+': ('ADD', '__add__'),
        '+=': ('ADD_ASS', '__iadd__'),
        '-': ('SUB', '__sub__'),
        '-=': ('SUB_ASS', '__isub__'),
        '*': ('MUL', '__mul__'),
        '*=': ('MUL_ASS', '__imul__'),
        '/': ('DIV', '__div__'),
        '/=': ('DIV_ASS', '__idiv__'),
        '=': ('ASS', None),
        '%': ('MOD', '__mod__'),
        'or': ('L_OR', None),
        'and': ('L_AND', None),
        '|': ('B_OR', '__or__'),
        '&': ('B_AND', '__and__'),
        '[]': ('IDX', '__getitem__'),
        '[]=': ('IDX_ASS', '__setitem__'),
        '>': ('GT', '__gt__'),
        '>=': ('GTE', '__ge__'),
        '<': ('LT', '__lt__'),
        '<=': ('LTE', '__le__'),
        '==': ('EQ', '__eq__'),
        '!=': ('NE', '__ne__'),
        # TODO: add more operators
        }

# Hey, we've got to load libgc!
GC = ctypes.CDLL(ctypes.util.find_library('gc'), ctypes.RTLD_GLOBAL)

class Library(ctypes.CDLL):
    def add_operator(self, op, restype, argtypes, member=None):
        # get the ooc function name
        ooc_op, py_special_name = OPERATORS[op]
        ooc_name = '__OP_%s_%s' % (ooc_op, '_'.join(a._name_ for a in argtypes))
        # get the operator function
        func = self[ooc_name]
        func.restype = restype
        # add the function as member if wished
        # return `self` if the function has no return type given
        if restype is None:
            def method(self, *args, **kwargs):
                func(self, *args, **kwargs)
                return self
        else:
            def method(self, *args, **kwargs):
                return func(self, *args, **kwargs)
        if member is not None:
            setattr(argtypes[0], member, method)
        # if possible, add a pythonic operator
        if py_special_name is not None:
            setattr(argtypes[0], py_special_name, method)

class KindOfClass(object):
    _name_ = None
    _library = None
    _fields_ = None
    _struct = None
    _methods_ = None
    _static_methods_ = None
    _constructors_ = None

    @classmethod
    def _add_predefined(cls):
        """
            add all predefined members in *_methods_*,
            *_static_methods_* and *_constructors_*.
        """
        if cls._methods_ is not None:
            for name, restype, argtypes in cls._methods_:
                cls.add_method(name, restype, argtypes)
        if cls._static_methods_ is not None:
            for name, restype, argtypes in cls._static_methods_:
                cls.add_static_method(name, restype, argtypes)
        if cls._constructors_ is not None:
            for suffix, argtypes in cls._constructors_:
                cls.add_constructor(suffix, argtypes)

    @classmethod
    def bind(cls, lib):
        cls._library = lib
        # add all predefined members
        cls._add_predefined()

    @property
    def contents(self):
        return ctypes.cast(self, ctypes.POINTER(type(self)._struct)).contents

    @classmethod
    def setup(cls):
        if cls._struct is None:
            cls._setup()

    @classmethod
    def _get_name(cls, name):
        basename = cls._name_
        if basename is None:
            basename = cls.__name__
        return '_'.join((basename, name))

    @classmethod
    def method(cls, name, restype=None, argtypes=None):
        cls.setup()
        if cls._library is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._library[name]
        # We'll just say the `this` pointer is a void pointer for convenience.
        func.argtypes = [ctypes.POINTER(None)]
        if restype is not None:
            func.restype = restype
        if argtypes is not None:
            func.argtypes.extend(argtypes)
        return func

    @classmethod
    def static_method(cls, name, restype=None, argtypes=None):
        cls.setup()
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

class Class(KindOfClass, ctypes.c_void_p):
    @classmethod
    def _setup(cls):
        if cls._name_ is None:
            cls._name_ = cls.__name__
        struct = type(cls.__name__ + 'Struct', (ctypes.Structure,), {})
        if cls._fields_ is None:
            cls._fields_ = []
        # TODO: bitfields??
        fields = struct._fields_ = [
                ('__super__', types.Object)
                ] + cls._fields_
#        struct._anonymous_ = ('__super__',)
        cls._struct = struct

class Cover(KindOfClass):
    @classmethod
    def _setup(cls):
        if cls._name_ is None:
            cls._name_ = cls.__name__
        struct = type(cls.__name__ + 'Struct', (ctypes.Structure,), {})
        if cls._fields_ is None:
            cls._fields_ = []
        # TODO: bitfields??
        struct._fields_ = cls._fields_
        cls._struct = struct

