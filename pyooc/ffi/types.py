import ctypes

from . import Cover, Module, Class as _Class

class Types(object):
    def __init__(self, lib):
        types = Module(lib, 'lang/types')

        self.Char = type("Char", (Cover, ctypes.c_char), {})
        self.Char.bind(types)

        self.UChar = type("UChar", (Cover, ctypes.c_ubyte), {})
        self.UChar.bind(types)

        self.WChar = type("WChar", (Cover, ctypes.c_wchar), {})
        self.WChar.bind(types)

        self.String = type("String", (Cover, ctypes.c_char_p), {})
        self.String.bind(types)

        self.Pointer = type("Pointer", (Cover, ctypes.c_void_p), {})
        self.Pointer.bind(types)

        self.Int = type("Int", (Cover, ctypes.c_int), {})
        self.Int.bind(types)

        self.UInt = type("UInt", (Cover, ctypes.c_uint), {})
        self.UInt.bind(types)

        self.Short = type("Short", (Cover, ctypes.c_short), {})
        self.Short.bind(types)

        self.UShort = type("UShort", (Cover, ctypes.c_ushort), {})
        self.UShort.bind(types)

        self.Long = type("Long", (Cover, ctypes.c_long), {})
        self.Long.bind(types)

        self.ULong = type("ULong", (Cover, ctypes.c_ulong), {})
        self.ULong.bind(types)

        self.LLong = type("LLong", (Cover, ctypes.c_longlong), {})
        self.LLong.bind(types)

        self.ULLong = type("ULLong", (Cover, ctypes.c_ulonglong), {})
        self.ULLong.bind(types)

        self.Float = type("Float", (Cover, ctypes.c_float), {})
        self.Float.bind(types)

        self.Double = type("Double", (Cover, ctypes.c_double), {})
        self.Double.bind(types)

        self.LDouble = type("LDouble", (Cover, ctypes.c_longdouble), {})
        self.LDouble.bind(types)

        self.Int8 = type("Int8", (Cover, ctypes.c_int8), {})
        self.Int8.bind(types)

        self.Int16 = type("Int16", (Cover, ctypes.c_int16), {})
        self.Int16.bind(types)

        self.Int32 = type("Int32", (Cover, ctypes.c_int32), {})
        self.Int32.bind(types)

        self.Int64 = type("Int64", (Cover, ctypes.c_int64), {})
        self.Int64.bind(types)

        self.UInt8 = type("UInt8", (Cover, ctypes.c_uint8), {})
        self.UInt8.bind(types)

        self.UInt16 = type("UInt16", (Cover, ctypes.c_uint16), {})
        self.UInt16.bind(types)

        self.UInt32 = type("UInt32", (Cover, ctypes.c_uint32), {})
        self.UInt32.bind(types)

        self.UInt64 = type("UInt64", (Cover, ctypes.c_uint64), {})
        self.UInt64.bind(types)

        self.Octet = type("Octet", (Cover, ctypes.c_uint8), {})
        self.Octet.bind(types)

        #self.Void = type("Void", (Cover, None), {})
        #self.Void.bind(types)
        # Hey Mr Void, I'm very sorry, but you are no cover.
        self.Void = None

        self.Bool = type("Bool", (Cover, ctypes.c_bool), {})
        self.Bool.bind(types)

        self.SizeT = type("SizeT", (Cover, ctypes.c_size_t), {})
        self.SizeT.bind(types)

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

        ObjectClassStruct._fields_ = [
            ('__super__', self.Class),
            ('__defaults__', ctypes.CFUNCTYPE(None, Object)),
            ('__destroy__', ctypes.CFUNCTYPE(None, Object)),
            ('instanceOf', ctypes.CFUNCTYPE(self.Bool, Object, Class)),
            ('__load__', ctypes.CFUNCTYPE(None)),
        ]
        ObjectClassStruct._anonymous_ = ['__super__']

        ClassClassStruct._fields_ = [
            ('__super__', ObjectClassStruct),
            ('alloc__class', ctypes.CFUNCTYPE(Object, Class)),
            ('inheritsFrom__class', ctypes.CFUNCTYPE(self.Bool, Class, Class)),
        ]
        ClassClassStruct._anonymous_ = ['__super__']

        ObjectStruct._fields_ = [
            ('class_', self.Class),
        ]

        ClassStruct._fields_ = [
            ('__super__', Object),
            ('instanceSize', self.SizeT),
            ('size', self.SizeT),
            ('name', self.String),
            ('super', self.Class),
        ]
        Class._anonymous_ = ['__super__']

        Object.bind(types)
        Class.bind(types)

    def setup(self):
        self.Class.setup()
        self.Object.setup()

