from pyooc.ffi import Class

def bind(lib):
    module = lib.get_module('text/Buffer')

    class Buffer(Class):
        _methods_ = [
                ('append_chr', None, [lib.types.Char]),
                ('toString', lib.types.String, None),
        ]
        _constructors_ = [
                ('', None),
        ]

    Buffer.bind(module)

    module.Buffer = Buffer
    return module
