import ctypes

from . import Cover, Module, Class as _Class, KindOfClass

class Types(object):
    def __init__(self, lib):
        types = Module(lib, 'lang/types')
        numbers = Module(lib, 'lang/Numbers')
        string = Module(lib, 'lang/String')
        character = Module(lib, 'lang/Character')
        buffer_ = Module(lib, 'lang/Buffer')
        iterators = Module(lib, 'lang/Iterators')

        self.Char = type("Char", (Cover, ctypes.c_char), {})
        self.Char.bind(character, False)

        self.UChar = type("UChar", (Cover, ctypes.c_ubyte), {})
        self.UChar.bind(character, False)

        self.WChar = type("WChar", (Cover, ctypes.c_wchar), {})
        self.WChar.bind(character, False)

        class Iterable(_Class):
            _generictypes_ = ['T']

        self.Iterable = Iterable
        self.Iterable.bind(iterators, False)

        class Buffer(_Class):
            _extends_ = Iterable
            _fields_ = [
                ('size', ctypes.c_size_t),
                ('capacity', ctypes.c_size_t),
                ('mallocAddr', ctypes.c_char_p),
                ('data', ctypes.c_char_p),
            ]

        self.Buffer = Buffer
        Buffer.bind(buffer_, False)

        class String(_Class):
            _extends_ = Iterable
            _fields_ = [
                ('_buffer', Buffer),
            ]

            @classmethod
            def make(cls, s):
                return ctypes.cast(
                    cls._module.library.get_module('lang/String').makeStringLiteral(s, len(s)),
                    cls)

            def _get_value(self):
                return self.contents._buffer.contents.data

            def _set_value(self, value):
                self.contents._buffer = self.make(value).contents._buffer # TODO: please kill me

            value = property(_get_value, _set_value)

        self.String = String
        String.bind(string, False)

        self.Pointer = type("Pointer", (Cover, ctypes.c_void_p), {})
        self.Pointer.bind(types, False)

        self.Int = type("Int", (Cover, ctypes.c_int), {})
        self.Int.bind(numbers, False)

        self.UInt = type("UInt", (Cover, ctypes.c_uint), {})
        self.UInt.bind(numbers, False)

        self.Short = type("Short", (Cover, ctypes.c_short), {})
        self.Short.bind(numbers, False)

        self.UShort = type("UShort", (Cover, ctypes.c_ushort), {})
        self.UShort.bind(numbers, False)

        self.Long = type("Long", (Cover, ctypes.c_long), {})
        self.Long.bind(numbers, False)

        self.ULong = type("ULong", (Cover, ctypes.c_ulong), {})
        self.ULong.bind(numbers, False)

        self.LLong = type("LLong", (Cover, ctypes.c_longlong), {})
        self.LLong.bind(numbers, False)

        self.ULLong = type("ULLong", (Cover, ctypes.c_ulonglong), {})
        self.ULLong.bind(numbers, False)

        self.Float = type("Float", (Cover, ctypes.c_float), {})
        self.Float.bind(numbers, False)

        self.Double = type("Double", (Cover, ctypes.c_double), {})
        self.Double.bind(numbers, False)

        self.LDouble = type("LDouble", (Cover, ctypes.c_longdouble), {})
        self.LDouble.bind(numbers, False)

        self.Int8 = type("Int8", (Cover, ctypes.c_int8), {})
        self.Int8.bind(numbers, False)

        self.Int16 = type("Int16", (Cover, ctypes.c_int16), {})
        self.Int16.bind(numbers, False)

        self.Int32 = type("Int32", (Cover, ctypes.c_int32), {})
        self.Int32.bind(numbers, False)

        self.Int64 = type("Int64", (Cover, ctypes.c_int64), {})
        self.Int64.bind(numbers, False)

        self.UInt8 = type("UInt8", (Cover, ctypes.c_uint8), {})
        self.UInt8.bind(numbers, False)

        self.UInt16 = type("UInt16", (Cover, ctypes.c_uint16), {})
        self.UInt16.bind(numbers, False)

        self.UInt32 = type("UInt32", (Cover, ctypes.c_uint32), {})
        self.UInt32.bind(numbers, False)

        self.UInt64 = type("UInt64", (Cover, ctypes.c_uint64), {})
        self.UInt64.bind(numbers, False)

        self.Octet = type("Octet", (Cover, ctypes.c_uint8), {})
        self.Octet.bind(numbers, False)

        #self.Void = type("Void", (Cover, None), {})
        #self.Void.bind(types, False)
        # Hey Mr Void, I'm very sorry, but you are no cover.
        self.Void = None

        self.Bool = type("Bool", (Cover, ctypes.c_bool), {})
        self.Bool.bind(types, False)

        self.SizeT = type("SizeT", (Cover, ctypes.c_size_t), {})
        self.SizeT.bind(numbers, False)

        class Closure(Cover, ctypes.Structure):
            _fields_ = [
                ('thunk', ctypes.c_void_p),
                ('context', ctypes.c_void_p),
            ]

            @classmethod
            def from_func(cls, func, restype, argtypes):
                def wrapper(*args):
                    print 'CLOSURE ARGS:', args
                    return func(*(args[:-1]))
                argtypes = tuple(argtypes) + (ctypes.c_void_p,) # context pointer.
                functype = ctypes.CFUNCTYPE(restype, *argtypes)
                return Closure(
                    thunk=ctypes.cast(functype(wrapper), ctypes.c_void_p),
                    context=None)

        self.Closure = Closure
        self.Closure.bind(types, False)

        # METACLASS FUN
        class ObjectClassStruct(ctypes.Structure):
            pass

        class ClassClassStruct(ctypes.Structure):
            pass

        class ObjectClass(_Class):
            _is_meta = True
            _struct = ObjectClassStruct

        class ClassClass(_Class):
            _is_meta = True
            _struct = ClassClassStruct

        class ObjectStruct(ctypes.Structure):
            pass

        class ClassStruct(ctypes.Structure):
            pass

        class Object(_Class):
            _meta = ObjectClass
            _struct = ObjectStruct

        self.Object = Object

        class Class(_Class):
            _meta = ClassClass
            _struct = ClassStruct

        self.Class = Class

        ClassStruct._fields_ = [
            ('__super__', Object),
            ('instanceSize', self.SizeT),
            ('size', self.SizeT),
            ('name', self.String),
            ('super', self.Class),
        ]
        ClassStruct._anonymous_ = ['__super__']

        ObjectClassStruct._fields_ = [
            ('__super__', ClassStruct),
            ('__defaults__', ctypes.CFUNCTYPE(None, Object)),
            ('__destroy__', ctypes.CFUNCTYPE(None, Object)),
            ('instanceOf__quest', ctypes.CFUNCTYPE(self.Bool, Object, Class)),
            ('__load__', ctypes.CFUNCTYPE(None)),
        ]
        ObjectClassStruct._anonymous_ = ['__super__']

        ClassClassStruct._fields_ = [
            ('__super__', ObjectClassStruct),
            ('alloc__class', ctypes.CFUNCTYPE(Object, Class)),
            ('inheritsFrom__quest__class', ctypes.CFUNCTYPE(self.Bool, Class, Class)),
        ]
        ClassClassStruct._anonymous_ = ['__super__']

        ObjectStruct._fields_ = [
            ('class_', self.Class),
        ]

        Object.bind(types, False)
        Class.bind(types, False)

    def setup(self):
        self.Class.setup()
        self.Object.setup()
        for prop in self.__dict__.itervalues():
            try:
                if (issubclass(prop, KindOfClass)
                    and prop not in (self.Class, self.Object)):
                    prop.setup()
            except TypeError:
                pass
