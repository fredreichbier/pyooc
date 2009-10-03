import pyooc

lib = pyooc.Library('./libtest.so')

class Test(pyooc.GenericClass):
    _generic_types_ = ['T']

Test.bind(lib)

