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

class Func(object):
    def __init__(self,
            name,
            restype=None,
            argtypes=None,
            generictypes=None,
            static=False,
            overrides=False):
        name = name.replace('~', '_')
        if argtypes is None:
            argtypes = []
        self.name = name
        self.restype = restype
        self.argtypes = argtypes
        self.generictypes = generictypes
        self.static = static
        self.overrides = overrides

# Hey, we've got to load libgc!
GC = ctypes.CDLL(ctypes.util.find_library('gc'), ctypes.RTLD_GLOBAL)

_CData = ctypes._SimpleCData.__bases__[0] # I now feel evil.

class Library(ctypes.CDLL):
    def __init__(self, *args, **kwargs):
        ctypes.CDLL.__init__(self, *args, **kwargs)
        self.types = types.Types(self)
        #: We're storing the class pointer -> pyooc class connection here.
        self._classes = {}
        self._module_cache = {}

        self.types.setup()

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

    def convert_arguments(self, args):
        return map(self.convert_to_ctypes, args)

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
            return self.library.types.String.make(value)
#        elif isinstance(value, unicode):
#            return ctypes.c_wchar_p(value)
        elif hasattr(value, '_as_parameter_'):
            return value._as_parameter_
        elif isinstance(value, _CData):
            return value
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

    def global_variable(self, name, type):
        return type.in_dll(self.library, self.member_prefix + name)

    def generic_function(self, name, generictypes, restype, argtypes=(), method=False, additional_generictypes=()):
        """
            Create a wrapper for a generic function. That can also be used for non-generic
            or generic multi-return functions. Didn't want too much code duplication, you know.
        """
        multi_return = isinstance(restype, tuple)
        # `additional_generictypes` are generic typenames that don't get passed.
        if argtypes is None:
            argtypes = []
        # is the return value a generic type? if yes, the
        # ooc-generated function looks a bit different :)
        if not multi_return:
            return_generic = (restype in generictypes or restype in additional_generictypes)
            multi_return_generic = False
        else:
            # For multi-return functions, this is always False.
            return_generic = False
            multi_return_generic = True
        # get the method
        func = self[name]
        # now construct the argument list.
        pass_argtypes = []
        # if it's a method, the this pointer is the very first argument.
        if method:
            pass_argtypes.append(ctypes.c_void_p)
        # if it's a multi-return function, now we get pointers to the return values.
        if multi_return:
            for rtype in restype:
                if (rtype in generictypes or rtype in additional_generictypes):
                    pass_argtypes.append(ctypes.POINTER(ctypes.POINTER(self.library.types.Octet)))
                else:
                    pass_argtypes.append(ctypes.POINTER(rtype))
        # if the return value is a generic, the first argument will
        # be a pointer to the return value
        if return_generic:
            pass_argtypes.append(ctypes.c_void_p)
        # ooc's generic functions take the classes of the template
        # types as first arguments. Say it's void* for simplicity.
        for _ in generictypes:
            pass_argtypes.append(ctypes.c_void_p)
        # then all arguments follow
        for argtype in argtypes:
            # a templated argtype will be a pointer to a value.
            if (argtype in generictypes or argtype in additional_generictypes):
                pass_argtypes.append(ctypes.POINTER(self.library.types.Octet))
            elif argtype == self.library.types.Class:
                # special-case class to make ctypes accept `pyooc.ffi.Class`. TODO?
                pass_argtypes.append(Class)
            else:
                pass_argtypes.append(argtype)
        # yep, it's ready.
        func.argtypes = pass_argtypes
        # functions with generic return values don't have a return value in C,
        # same for multi-return functions.
        if not (return_generic or multi_return):
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
            generictypes_types = {}
            if multi_return:
                multi_return_values = []
                # Multiple, partly generic return types.
                for ridx, rtype in enumerate(restype):
                    if (rtype in generictypes or rtype in additional_generictypes):
                        # Generic, yes.
                        if (method and rtype in additional_generictypes):
                            # See above.
                            restype_ = getattr(pass_args[0].contents, rtype)
                            result = self.library._get_class_type(restype_)()
                        else:
                            restype_ = kwargs.pop('restype%d' % ridx)
                            assert restype_ # TODO: COOL error
                            result = restype_()
                            if rtype not in generictypes_types:
                                generictypes_types[rtype] = restype_.class_()
                        pass_args.append(ctypes.cast(
                            ctypes.pointer(ctypes.pointer(result)),
                            ctypes.POINTER(ctypes.POINTER(self.library.types.Octet))
                            ))
                    else:
                        # Ordinary.
                        result = rtype()
                        pass_args.append(ctypes.pointer(result))
                    multi_return_values.append(result)
                assert not kwargs
            # if the return value is generic or, the user has to pass the type explicitly.
            if return_generic:
                restype_ = None
                if (method and restype in additional_generictypes):
                    # Yay generic type restype AND a method AND class-wide
                    # generic type. TODO: BAH EVILNESS
                    restype_ = getattr(pass_args[0].contents, restype)
                    # allocate some memory for dinner
                    result = self.library._get_class_type(restype_)()
                else:
                    restype_ = kwargs.pop('restype')
                    assert not kwargs
                    assert restype_ # TODO: nice error
                    result = restype_()
                    # TODO: Since we have to pass the result type anyway, we could work around
                    # the rock limitation that you have to pass the class explicitly if you have
                    # a function with a generic return value (ie. `a: func <T> (T: Class) -> T`). Hmmm?
                pass_args.append(ctypes.pointer(result))
            regular_args = []
            for argtype, arg in zip(argtypes, args):
                # is it generic?
                arg = self.convert_to_ctypes(arg)
                if (argtype in generictypes or argtype in additional_generictypes):
                    # yes. pass a pointer.
                    regular_args.append(
                            ctypes.cast(
                                ctypes.pointer(arg),
                                ctypes.POINTER(
                                    self.library.types.Octet
                                    )
                                ))
                    if argtype not in generictypes_types:
                        generictypes_types[argtype] = arg.class_()
                else:
                    # no. just pass the argument.
                    regular_args.append(arg)
            for gtype in generictypes:
                pass_args.append(generictypes_types[gtype])
            pass_args.extend(regular_args)
            # and now ... call it!
            if return_generic:
                func(*pass_args)
                return result
            elif multi_return:
                func(*pass_args)
                return tuple(multi_return_values)
            else:
                return func(*pass_args)
        return function

class KindOfClass(object):
    _name_ = None
    _module = None
    _fields_ = None
    _static_fields_ = None
    _struct = None
    _methods_ = None
    _generictypes_ = None
    _extends_ = None
    _meta = None
    _is_meta = None

    @classmethod
    def class_(cls):
        """
            oh yay, return my class
        """
        return cls._static_method('class', cls._meta)()

    @classmethod
    def bind(cls, module, autosetup=True):
        assert isinstance(module, Module)
        cls._module = module
        if autosetup:
            cls.setup()

    @classmethod
    def setup(cls):
        if cls._struct is None:
            if cls._generictypes_ is None:
                cls._generictypes_ = ()
            if (not cls._is_meta and cls._meta is None):
                cls._create_meta()
                cls._meta.setup()
            cls._setup()

    @classmethod
    def _get_name(cls, name):
        basename = cls._name_
        if basename is None:
            basename = cls.__name__
        return '_'.join((basename, name))

    def get_generic_member(self, name):
        """
            Return the value of the generic member *name*, correctly typed.
        """
        typename = dict(type(self)._generic_members)[name]
        typevalue = getattr(self.contents, typename)
        value = getattr(self.contents, name)
        typ = type(self)._module.library._get_class_type(typevalue)
        return ctypes.cast(value, ctypes.POINTER(typ)).contents

    @classmethod
    def _generic_method(cls, name, generictypes, restype=None, argtypes=None):
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        # We'll just say the `this` pointer is a void pointer for convenience.
        # That's now done by `generic_function`
        #argtypes = [ctypes.POINTER(None)] + argtypes
        return cls._module.generic_function(name, generictypes, restype, argtypes,
                                            True, cls._generictypes_)
    @classmethod
    def _generic_static_method(cls, name, generictypes, restype=None, argtypes=None):
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        return cls._module.generic_function(name, generictypes, restype, argtypes,
                                            False, cls._generictypes_)

    @classmethod
    def _method(cls, name, restype=None, argtypes=None):
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._module[name]
        if restype is not None:
            if (restype in cls._generictypes_ or isinstance(restype, tuple)):
                # Generic or multi-return function.
                return cls._module.generic_function(name, (), restype, argtypes, True, cls._generictypes_)
            else:
                func.restype = restype
        if argtypes is not None:
            if any(a in cls._generictypes_ for a in argtypes):
                # gooonoroc!
                return cls._module.generic_function(name, (), restype, argtypes, True, cls._generictypes_)
            else:
                func.argtypes = [ctypes.POINTER(None)] + argtypes
        else:
            func.argtypes = [ctypes.POINTER(None)]
        def call(*args):
            return func(*cls._module.convert_arguments(args))
        return call

    @classmethod
    def _static_method(cls, name, restype=None, argtypes=None):
        if cls._module is None:
            raise BindingError("You have to bind the class to a library!")
        name = cls._get_name(name)
        func = cls._module[name]
        if restype is not None:
            if (restype in cls._generictypes_ or isinstance(restype, tuple)):
                # Generic or multi-return function.
                return cls._module.generic_function(name, (), restype, argtypes, False, cls._generictypes_)
            else:
                func.restype = restype
        if argtypes is not None:
            if any(a in cls._generictypes_ for a in argtypes):
                # gooonoroc!
                return cls._module.generic_function(name, (), restype, argtypes, False, cls._generictypes_)
            else:
                func.argtypes = argtypes
        def call(*args):
            return func(*cls._module.convert_arguments(args))
        return call

    @classmethod
    def _create_meta(cls):
        """
            Create the metaclass and store it.
        """
        if cls is cls._module.library.types.Object:
            extends = cls._module.library.types.Class
        elif cls is cls._module.library.types.Class:
            extends = cls._module.library.types.Object._meta
        elif cls._extends_ in (cls._module.library.types.Object, None):
            # Object's direct descendants' metaclasses extend `ClassClass`.
            extends = cls._module.library.types.Class._meta
        elif cls._extends_:
            extends = cls._extends_._meta
        else:
            extends = None
        cls._meta = type(cls.__name__ + 'Class', (Class,), {
            '_is_meta': cls,
            '_extends_': extends,
            '_fields_': cls._static_fields_, # TODO: add function pointers
        })
        cls._meta.bind(cls._module)

    @classmethod
    def _add_method(cls, name, *args, **kwargs):
        ctypes_meth = cls._method(name, *args, **kwargs)
        def method(self, *args, **kwargs):
            return ctypes_meth(self, *args, **kwargs)
        setattr(cls, name, method)

    @classmethod
    def _add_generic_method(cls, name, generic_types, *args, **kwargs):
        ctypes_meth = cls._generic_method(name, generic_types, *args, **kwargs)
        def method(self, *args, **kwargs):
            return ctypes_meth(self, *args, **kwargs)
        setattr(cls, name, method)

    @classmethod
    def _add_generic_static_method(cls, name, generic_types, *args, **kwargs):
        ctypes_meth = cls._generic_static_method(name, generic_types, *args, **kwargs)
        setattr(cls, name, staticmethod(ctypes_meth))

    @classmethod
    def _add_static_method(cls, name, *args, **kwargs):
        ctypes_meth = cls._static_method(name, *args, **kwargs)
        setattr(cls, name, staticmethod(ctypes_meth))

class Class(KindOfClass, ctypes.c_void_p):
    @property
    def contents(self):
        return ctypes.cast(self, ctypes.POINTER(type(self)._struct)).contents

    @classmethod
    def _setup(cls):
        dct = {}
        if cls._name_ is None:
            cls._name_ = cls.__name__
        if cls._fields_ is None:
            cls._fields_ = []
        cls._generic_members = []
        # Super type?
        if (cls._extends_ is not None and cls._extends_ != cls._module.library.types.Object):
            if not issubclass(cls._extends_, Class):
                raise BindingError("%r is not a valid super-type for %r" % (cls._extends_, cls))
            cls.__bases__ = (cls._extends_,)
            cls._extends_.setup()
            super_type = cls._extends_._struct
        else:
            super_type = cls._module.library.types.Object._struct
        if cls is cls._module.library.types.Object:
            fields = []
            anon = []
        else:
            fields = [('__super__', super_type)]
            anon = ['__super__']
        # add the Class pointers. They are done in the reverse order.
        for typename in cls._generictypes_[::-1]:
            fields.append(
                    (typename, cls._module.library.types.Class)
                    )
        # Do the ordinary fields. For the metaclass, these are the static fields
        # of the "real" class.
        for row in cls._fields_[:]:
            if len(row) == 2:
                # ordinary field.
                name, argtype = row
                if argtype in cls._generictypes_:
                    fields.append(
                        (name, ctypes.POINTER(cls._module.library.types.Octet))
                        )
                    cls._generic_members.append((name, argtype))
                else:
                    fields.append((name, argtype))
            else:
                # property!
                name, argtype, getter_name, setter_name = row
                real_name = '_%s_' % name
                getter = None
                setter = None
                if getter_name:
                    getter = cls._module.library[getter_name]
                    getter.restype = argtype
                    if cls._is_meta: # they're static!
                        getter.argtypes = []
                        getter = lambda self, g=getter: g()
                    else:
                        getter.argtypes = [cls]
                        # `X` should be `this`, not `XStruct`.
                        getter = lambda self, g=getter: g(ctypes.byref(self))
                if setter_name:
                    setter = cls._module.library[setter_name]
                    if cls._is_meta: # it's static.
                        setter.argtypes = [argtype]
                        setter = lambda self, value, s=setter: s(value)
                    else:
                        setter.argtypes = [ctypes.c_void_p, argtype]
                        setter = lambda self, value, s=setter: s(ctypes.byref(self), value)
                dct[name] = property(getter, setter)
                fields.append((real_name, argtype))
        # In case we're a metaclass, add the function table.
        if cls._is_meta is not None:
            client = cls._is_meta # get the "real" class.
            # All functions, if static, constructors or ordinary, are
            # just added in the order they were defined.
            if client._methods_:
                for func in client._methods_:
                    # Let's add it to the Python class ...
                    if func.static:
                        if func.generictypes:
                            client._add_generic_static_method(func.name, func.generictypes, func.restype, func.argtypes)
                        else:
                            client._add_static_method(func.name, func.restype, func.argtypes)
                    else:
                        if func.generictypes:
                            client._add_generic_method(func.name, func.generictypes,
                                                       func.restype, func.argtypes)
                        else:
                            client._add_method(func.name, func.restype, func.argtypes)
                    # ... and now to the ctypes struct -- if it's not an overriding method.
                    # (ie. already in an ancestor's struct)
                    if not func.overrides:
                        fields.append((func.name, ctypes.CFUNCTYPE(None))) # TODO: be more specific. work around problems with generic types!
        dct.update({
            '_anonymous_': anon,
            '_fields_': fields,
        })
        struct = type(ctypes.Structure)(cls.__name__ + 'Struct', (ctypes.Structure,), dct)
        cls._struct = struct
        # connect the ooc class to the python class
        if not cls._is_meta:
            cls._module.library._add_class_type(cls.class_(), cls)

class Cover(KindOfClass):
    @classmethod
    def _setup(cls):
        if cls._name_ is None:
            cls._name_ = cls.__name__
        if cls._fields_ is None:
            cls._fields_ = []
        bases = (ctypes.Structure,)
        if cls._extends_ is not None:
            bases = (cls._extends_._struct,)
            cls.__bases__ = (cls._extends,)
        struct = type(cls.__name__ + 'Struct', bases, {
            '_fields_': cls._fields_,
        })
        cls._struct = struct
        # connect the ooc class to the python class
        cls._module.library._add_class_type(cls.class_(), cls)

# We import it here because types.py needs Cover.
from . import types
