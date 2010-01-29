import pyooc

lib = pyooc.Library('./libtest.so')
mod = lib.get_module('test')

class Greeter(pyooc.Class):
    _methods_ = [
            ('greet', None, None),
        ]
    _fields_ = [
            ('msg', lib.types.String),
        ]
    _constructors_ = [
            ('', [lib.types.String]),
        ]

Greeter.bind(mod)

greeter = Greeter.new('You')
greeter.greet()

print greeter.contents.msg.value
