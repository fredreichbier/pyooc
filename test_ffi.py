import pyooc.ffi as ffi

lib = ffi.Library('./libtest.so')

class Greeter(ffi.Class):
    _methods_ = [
        ('greet', None, None),
    ]
    _constructors_ = [
        ('', [lib.types.String])
    ]

class AnotherCell(ffi.Class):
    _generic_types_ = ['T']
    _methods_ = [
        ('setValue', None, 'T'),
        ('getValue', 'T', None),
    ]
    _constructors_ = [
        ('', ['T']),
    ]

mod = lib.get_module('test')

Greeter.bind(mod)
AnotherCell.bind(mod)

g = Greeter.new('Mr Banana')
g.greet()

cell = AnotherCell.new(lib.types.String.class_(), 'Hellow')
cell.setValue('Wolleh')
print cell.getValue().value
