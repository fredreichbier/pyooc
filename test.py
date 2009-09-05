import pyooc
from pyooc import types

lib = pyooc.Library('./libtest.so')

class Yay(pyooc.KindOfClass):
    pass

Yay.bind(lib)
Yay.add_static_method('new', Yay)
Yay.add_method('hello')

yay = Yay.new()
yay.hello()

