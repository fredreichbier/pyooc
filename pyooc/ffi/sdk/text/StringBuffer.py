from pyooc.ffi import Class

def bind(lib):
    module = lib.get_module('text/StringBuffer')

    class StringBuffer(Class):
        _methods_ = [
                ('write_chr', None, [lib.types.Char]),
                ('toString', lib.types.String, None),
        ]
        _constructors_ = [
                ('', None),
        ]

    StringBuffer.bind(module)

    module.StringBuffer = StringBuffer
    return module
