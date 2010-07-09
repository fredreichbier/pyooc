import pyooc.ffi as ffi

lib = ffi.Library('./libtest.so')

class Greeter(ffi.Class):
    _fields_ = [
        ('msg', lib.types.String),
    ]
    _methods_ = [
        ('greet', None, None),
    ]
    _constructors_ = [
        ('', [lib.types.String])
    ]

class BetterGreeter(ffi.Class):
    _extends_ = Greeter

    _fields_ = [
        ('count', lib.types.Int),
    ]
    _constructors_ = [
        ('better', [lib.types.String, lib.types.Int]),
    ]

class AnotherCell(ffi.Class):
    _generic_types_ = ['T']

    _methods_ = [
        ('setValue', None, ['T']),
        ('getValue', 'T', None),
    ]
    _constructors_ = [
        ('', ['T']),
    ]

mod = lib.get_module('test')

Greeter.bind(mod)
BetterGreeter.bind(mod)
AnotherCell.bind(mod)

g = Greeter.new('Mr Banana')
g.greet()
print g.contents.msg.value

b = BetterGreeter.new_better('Mr Sausage', 1337)
b.greet()
print b.contents.msg.value
print b.contents.count.value
