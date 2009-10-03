import pyooc

lib = pyooc.Library('./libtest.so')
lib._test_load = lib._test_load
lib._test_load()

class Test(pyooc.GenericClass):
    _generic_types_ = ['T']
    _fields_ = [
        ('message', 'T'),
    ]
    _constructors_ = [
        ('', [lib.types.String])
    ]

Test.bind(lib)
Test.add_method('printy')

test = Test.new(lib.types.String.class_(), 'heeeeeeeya')
test.printy()
print test.get_generic_member('message').value
