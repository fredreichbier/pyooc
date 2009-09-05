import pyooc
from pyooc import types

lib = pyooc.Library('./libtest.so')

class Yay(pyooc.Class):
    pass

Yay.bind(lib)
Yay.add_constructor()
Yay.add_method('hello ~there')

yay = Yay.new()
yay['hello~there']()

