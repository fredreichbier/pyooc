import ctypes
import ctypes.util
import re
from functools import partial

class BindingError(Exception):
    pass

CTYPES_BASE_TYPE = type(ctypes.c_char_p)

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
    def __init__(self, *args, **kwargs):
        ctypes.CDLL.__init__(self, *args, **kwargs)
        self.types = types.Types(self)
        #: We're storing the class pointer -> pyooc class connection here.
        self._classes = {}
        self._module_cache = {}

    def get_module(self, path, autoload=True):
        # TODO: respect autoload?
        if path not in self._module_cache:
            self._module_cache[path] = Module(self, path, autoload)
        return self._module_cache[path]

    def _add_class_type(self, ooc, py):
        address = ctypes.addressof(ooc.contents)
        self._classes[address] = py

    def _get_class_type(self, ooc):
        address = ctypes.addressof(ooc.contents)
        return self._classes[address]

class Module(object):
    def __init__(self, library, path, autoload=True):
        self.library = library
        self.path = path
        self.member_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', path) + '__'
        if re.match(r'^[^a-zA-Z0-9_]', self.member_prefix):
            self.member_prefix = '_' + self.member_prefix
        if autoload:
            self.load()

    def load(self):
        """
            Call the "%s_load" % member_prefix[:-2] function.
            (module "lang/types" -> "lang_types_load")
        """
        load = self.library['%s_load' % self.member_prefix[:-2]]
        load()

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        return self.library[self.member_prefix + key]

    def convert_to_ctypes(self, value):
        if value is None:
            return self.library.types.Pointer()
        elif isinstance(value, (Class, Cover)):
            return value
        elif isinstance(value, int):
            return self.library.types.Int(value)
        elif isinstance(value, long):
            return self.library.types.Long(value) # TODO: unsigned?
        elif isinstance(value, str):
            return self.library.types.String(value)
#        elif isinstance(value, unicode):
#            return ctypes.c_wchar_p(value)
        elif hasattr(value, '_as_parameter_'):
            return value._as_parameter_
        else:
            raise BindingError("No idea how to convert %r" % value)

    def add_operator(self, op, restype, argtypes, add_operator=True, member=None):
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
        if (add_operator and py_special_name is not None):
            setattr(argtypes[0], py_special_name, method)
        return method

    def generic_function(self, name, generic_types, restype, argtypes=(), method=False, additional_generic_types=()):
        # `additional_generic_types` are generic typenames that don't get passed.
        if argtypes is None:
            argtypes = []
        # is the return value a generic type? if yes, the
        # ooc-generated function looks a bit different :)
        return_generic = (restype in generic_types or restype in additional_generic_types)
        # get the method
        func = self[name]
        # now construct the argument list.
        pass_argtypes = []
        # if it's a method, the this pointer is the very first argument.
        if method:
            pass_argtypes.append(ctypes.c_void_p)
        # if the return value is a generic, the first argument will
        # be a pointer to the return value
        if return_generic:
            pass_argtypes.append(ctypes.c_void_p)
        # ooc's generic functions take the classes of the template
        # types as first arguments.
        for _ in generic_types:
            pass_argtypes.append(ctypes.POINTER(self.library.types.Class))
        # then all arguments follow
        for argtype in argtypes:
            # a templated argtype will be a pointer to a value.
            if (argtype in generic_types or argtype in additional_generic_types):
                pass_argtypes.append(ctypes.POINTER(self.library.types.Octet))
            else:
                pass_argtypes.append(argtype)
        # yep, it's ready.
        func.argtypes = pass_argtypes
        # functions with generic return values don't have a return value in C
        if not return_generic:
            func.restype = restype
        # Now, we'll construct a function. It's not very nice,
        # I'd rather like to generate code, but that would
        # be evil, I think. TODO: nicer nicer nicer!
        def function(*args, **kwargs):
            pass_args = []
            # if it's a method, the first argument is
            # the this pointer.
            if method:
                pass_args.append(args[0])
                args = args[1:]
            # if the return value is generic, the user has to
            # pass the type explicitly.
            if return_generic:
                if (method and restype in additional_generic_types):
                    # Yay generic type restype AND a method AND class-wide
                    # generic type. TODO: BAH EVILNESS
                    restype_ = getattr(pass_args[0].contents, restype)
                    # allocate some memory for dinner
                    result = self.library._get_class_type(restype_)()
                    pass_args.append(ctypes.pointer(result))
                else:
                    restype_ = kwargs.pop('restype')
                    assert not kwargs
                    assert restype_ # TODO: nice error
                    result = restype_()
                    pass_args.append(ctypes.pointer(result))
            generic_types_types = {}
            regular_args = []
            for argtype, arg in zip(argtypes, args):
                # is it generic?
                arg = self.convert_to_ctypes(arg)
                if (argtype in generic_types or argtype in additional_generic_types):
                    # yes. pass a pointer.
                    regular_args.append(
                            ctypes.cast(
                                ctypes.pointer(arg),
                                ctypes.POINTER(
                                    self.library.types.Octet
                                    )
                                ))
                    if argtype not in generic_types_types:
                        generic_types_types[argtype] = arg.class_()
                else:
                    # no. just pass the argument.
                    regular_args.append(arg)
            for gtype in generic_types:
                pass_args.append(generic_types_types[gtype])
            pass_args.extend(regular_args)
            # and now ... call it!
            if return_generic:
                func(*pass_args)
                return result
            else:
                return func(*pass_args)
        return function

class KindOfClass(object):
    _name_ = None
    _module = None
    _fields_ = None
    _struct = None
    _methods_ = None
    _static_methods_ = None
    _generic_methods_ = None
    _constructors_ = None

    @classmethod
    def class_(cls):
        """
            oh yay, return my class
        """
        r = cls.static_method('class',
                ctypes.POINTER(cls._module.library.types.Class)
                )()
        return r

    @classmethod
    def _add_predefined(cls):
        """
            add all predefined members in *_methods_*,
            *_static_methods_*, *_generic_methods_* and *_constructors_*.
        """
        if cls._methods_ is not None:
            for name, restype, argtypes in cls._methods_:
                cls.add_method(name, restype, argtypes)
        if cls._static_methods_ is not None:
            for name, restype, argtypes in cls._static_methods_:
                cls.add_static_method(name, restype, argtypes)
        if cls._generic_methods_ is not None:
            for name, generic_types, restype, argtypes in cls._generic_methods_:
                cls.add_generic_method(name, generic_types, restype, argtypes)
        if cls._constructors_ is not None:
            for suffix, argtypes in cls._constructors_:
                cls.add_constructor(suffix, argtypes)

    @classmethod
    def bind(cls, module):
        assert isinstance(module, Module)
        cls._module = module
        # add all predefined members
        cls._add_predefined()

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
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._module[name]
        # We'll just say the `this` pointer is a void pointer for convenience.
        if restype is not None:
            func.restype = restype
        if argtypes is not None:
            func.argtypes = [ctypes.POINTER(None)] + argtypes
        else:
            func.argtypes = [ctypes.POINTER(None)]
        return func

    @classmethod
    def generic_method(cls, name, generic_types, restype=None, argtypes=None):
        cls.setup()
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        # We'll just say the `this` pointer is a void pointer for convenience.
        # That's now done by `generic_function`
        #argtypes = [ctypes.POINTER(None)] + argtypes
        return cls._module.generic_function(name, generic_types, restype, argtypes, True)

    @classmethod
    def static_method(cls, name, restype=None, argtypes=None):
        cls.setup()
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._module[name]
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
    def add_generic_method(cls, name, generic_types, *args, **kwargs):
        ctypes_meth = cls.generic_method(name, generic_types, *args, **kwargs)
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
    @property
    def contents(self):
        return ctypes.cast(self, ctypes.POINTER(type(self)._struct)).contents

    @classmethod
    def _setup(cls):
        if cls._name_ is None:
            cls._name_ = cls.__name__
        struct = type(cls.__name__ + 'Struct', (ctypes.Structure,), {})
        if cls._fields_ is None:
            cls._fields_ = []
        # TODO: bitfields??
        fields = struct._fields_ = [
                ('__super__', cls._module.library.types.Object)
                ] + cls._fields_
#        struct._anonymous_ = ('__super__',)
        cls._struct = struct
        # connect the ooc class to the python class
        cls._module.library._add_class_type(cls.class_(), cls)

class GenericClass(Class):
    _generic_types_ = ()

    @classmethod
    def _setup(cls):
        if cls._name_ is None:
            cls._name_ = cls.__name__
        if not cls._generic_types_:
            raise BindingError("%s is a generic class, but has no generic types set" % cls.__name__)
        struct = type(cls.__name__ + 'Struct', (ctypes.Structure,), {})
        if cls._fields_ is None:
            cls._fields_ = []
        fields = []
        cls._generic_members_ = []
        # add the Class pointers. They are done in the reverse order.
        for typename in cls._generic_types_[::-1]:
            fields.append(
                    (typename, ctypes.POINTER(cls._module.library.types.Class))
                    )
        for name, argtype in cls._fields_[:]:
            if argtype in cls._generic_types_:
                fields.append(
                    (name, ctypes.POINTER(cls._module.library.types.Octet))
                    )
                cls._generic_members_.append((name, argtype))
            else:
                fields.append((name, argtype))
        # TODO: bitfields??
        fields = struct._fields_ = [
                ('__super__', cls._module.library.types.Object)
                ] + fields
#        struct._anonymous_ = ('__super__',)
        cls._struct = struct
        # connect the ooc class to the python class
        cls._module.library._add_class_type(cls.class_(), cls)

    @classmethod
    def constructor(cls, suffix='', argtypes=None):
        """
            Here, we have to pass the generic types in the arguments.
        """
        if suffix:
            name = 'new_' + suffix
        else:
            name = 'new'
        type_argtypes = [ctypes.POINTER(cls._module.library.types.Class) for _ in cls._generic_types_]
        if argtypes is None:
            argtypes = []
        return cls.static_method(name, cls, type_argtypes + argtypes)

    def get_generic_member(self, name):
        """
            Return the value of the generic member *name*, correctly typed.
        """
        typename = dict(type(self)._generic_members_)[name]
        typevalue = getattr(self.contents, typename)
        value = getattr(self.contents, name)
        typ = type(self)._module.library._get_class_type(typevalue)
        return ctypes.cast(value, ctypes.POINTER(typ)).contents

    @classmethod
    def generic_method(cls, name, generic_types, restype=None, argtypes=None):
        cls.setup()
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        # We'll just say the `this` pointer is a void pointer for convenience.
        # That's now done by `generic_function`
        #argtypes = [ctypes.POINTER(None)] + argtypes
        return cls._module.generic_function(name, generic_types, restype, argtypes,
                                            True, cls._generic_types_)

    @classmethod
    def method(cls, name, restype=None, argtypes=None):
        cls.setup()
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._module[name]
        if restype is not None:
            if restype in cls._generic_types_:
                # ggggeneric function!
                return cls._module.generic_function(name, (), restype, argtypes, True, cls._generic_types_)
            else:
                func.restype = restype
        if argtypes is not None:
            if any(a in cls._generic_types_ for a in argtypes):
                # gooonoroc!
                return cls._module.generic_function(name, (), restype, argtypes, True, cls._generic_types_)
            else:
                func.argtypes = [ctypes.POINTER(None)] + argtypes
        else:
            func.argtypes = [ctypes.POINTER(None)]
        return func

    @classmethod
    def static_method(cls, name, restype=None, argtypes=None):
        cls.setup()
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._module[name]
        if restype is not None:
            if restype in cls._generic_types_:
                # ggggeneric function!
                return cls._module.generic_function(name, (), restype, argtypes, True, cls._generic_types_)
            else:
                func.restype = restype
        if argtypes is not None:
            if any(a in cls._generic_types_ for a in argtypes):
                # gooonoroc!
                return cls._module.generic_function(name, (), restype, argtypes, True, cls._generic_types_)
            else:
                func.argtypes = argtypes
        return func

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
        # connect the ooc class to the python class
        cls._module.library._add_class_type(cls.class_(), cls)

# We import it here because types.py needs Cover.
from . import types
