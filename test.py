import pyooc
from pyooc import types

lib = pyooc.Library('./libtest.so')

class Yay(pyooc.Class):
    pass

Yay.bind(lib)
Yay.add_constructor()
Yay.add_constructor('withMessage', [types.String])
Yay.add_method('greet')

with_ = Yay.new_withMessage("Huhu!")
with_.greet()

without = Yay.new()
without.greet()
