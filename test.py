import pyooc
from pyooc import types

lib = pyooc.Library('./libtest.so')

class String(pyooc.Cover, types.String):
    _methods_ = [
            # name      restype argtypes
            ('println', None,   None),
            ]

class Yay(pyooc.Class):
    _fields_ = [
            ('message', String),
            ]
    _methods_ = [
            ('greet', None, None)
            ]
    _constructors_ = [
            ('', None),
            ('withMessage', [types.String]),
            ]

Yay.bind(lib)
String.bind(lib)

gimmeAString = lib.gimmeAString
gimmeAString.restype = String

with_ = Yay.new_withMessage("Huhu!")
with_.greet()

without = Yay.new()
without.greet()

print 'I got the message:', with_.contents.message.value

with_.contents.message.println()
gimmeAString().println()

