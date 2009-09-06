import pyooc
from pyooc import types

lib = pyooc.Library('./libtest.so')

class String(pyooc.Cover, types.String):
    pass

class Yay(pyooc.Class):
    fields = [
            ('message', String),
            ]

Yay.bind(lib)
String.bind(lib)

Yay.add_constructor()
Yay.add_constructor('withMessage', [types.String])
Yay.add_method('greet')

with_ = Yay.new_withMessage("Huhu!")
with_.greet()

without = Yay.new()
without.greet()

print 'I got the message:', with_.contents.message.value

String.add_method('println')

with_.contents.message.println()
