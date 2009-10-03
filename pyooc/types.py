import ctypes

from . import Cover

class Types(object):
    def __init__(self, lib):
        self.Char = type("Char", (Cover, ctypes.c_char), {})
        self.Char.bind(lib)

        self.UChar = type("UChar", (Cover, ctypes.c_ubyte), {})
        self.UChar.bind(lib)

        self.WChar = type("WChar", (Cover, ctypes.c_wchar), {})
        self.WChar.bind(lib)

        self.String = type("String", (Cover, ctypes.c_char_p), {})
        self.String.bind(lib)

        self.Pointer = type("Pointer", (Cover, ctypes.c_void_p), {})
        self.Pointer.bind(lib)

        self.Int = type("Int", (Cover, ctypes.c_int), {})
        self.Int.bind(lib)

        self.UInt = type("UInt", (Cover, ctypes.c_uint), {})
        self.UInt.bind(lib)

        self.Short = type("Short", (Cover, ctypes.c_short), {})
        self.Short.bind(lib)

        self.UShort = type("UShort", (Cover, ctypes.c_ushort), {})
        self.UShort.bind(lib)

        self.Long = type("Long", (Cover, ctypes.c_long), {})
        self.Long.bind(lib)

        self.ULong = type("ULong", (Cover, ctypes.c_ulong), {})
        self.ULong.bind(lib)

        self.LLong = type("LLong", (Cover, ctypes.c_longlong), {})
        self.LLong.bind(lib)

        self.ULLong = type("ULLong", (Cover, ctypes.c_ulonglong), {})
        self.ULLong.bind(lib)

        self.Float = type("Float", (Cover, ctypes.c_float), {})
        self.Float.bind(lib)

        self.Double = type("Double", (Cover, ctypes.c_double), {})
        self.Double.bind(lib)

        self.LDouble = type("LDouble", (Cover, ctypes.c_longdouble), {})
        self.LDouble.bind(lib)

        self.Int8 = type("Int8", (Cover, ctypes.c_int8), {})
        self.Int8.bind(lib)

        self.Int16 = type("Int16", (Cover, ctypes.c_int16), {})
        self.Int16.bind(lib)

        self.Int32 = type("Int32", (Cover, ctypes.c_int32), {})
        self.Int32.bind(lib)

        self.Int64 = type("Int64", (Cover, ctypes.c_int64), {})
        self.Int64.bind(lib)

        self.UInt8 = type("UInt8", (Cover, ctypes.c_uint8), {})
        self.UInt8.bind(lib)

        self.UInt16 = type("UInt16", (Cover, ctypes.c_uint16), {})
        self.UInt16.bind(lib)

        self.UInt32 = type("UInt32", (Cover, ctypes.c_uint32), {})
        self.UInt32.bind(lib)

        self.UInt64 = type("UInt64", (Cover, ctypes.c_uint64), {})
        self.UInt64.bind(lib)

        self.Octet = type("Octet", (Cover, ctypes.c_uint8), {})
        self.Octet.bind(lib)

        #self.Void = type("Void", (Cover, None), {})
        #self.Void.bind(lib)
        # Hey Mr Void, I'm very sorry, but you are no cover.
        self.Void = None

        self.Bool = type("Bool", (Cover, ctypes.c_bool), {})
        self.Bool.bind(lib)

        self.SizeT = type("SizeT", (Cover, ctypes.c_size_t), {})
        self.SizeT.bind(lib)

        class Class(Cover, ctypes.Structure):
            pass

        self.Class = Class 
        # TODO: we can't derive from ctypes.POINTER(ctypes.ClassStruct)
        # - that is very sad :(
        # Wait: `Class` is a struct. Not a pointer to a struct. What do I
        # mean? OMGWTFBBQ?
        Class._fields_ = [
                ('class_', ctypes.POINTER(self.Class)),
                ('instanceSize', self.SizeT),
                ('size', self.SizeT),
                ('name', self.String),
                ('super', ctypes.POINTER(self.Class)),
                ]

        class ObjectStruct(ctypes.Structure):
            # Well, for the `Yay` class, there is `YayClass`, but
            # I think I'll just leave out that level of abstraction.
            # So, let's say there's only a pointer to a class.
            _fields_ = [
                    ('class_', ctypes.POINTER(self.Class)),
                ]

        self.Object = type("Object", (Cover, ctypes.POINTER(ObjectStruct)), {})
        self.Object.bind(lib)


