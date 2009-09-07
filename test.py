import pyooc

lib = pyooc.Library('./libtest.so')

class Yay(pyooc.Class):
    _constructors_ = [
            ('withMessage', [lib.types.String]),
            ('', None),
            ]
    _fields_ = [
            ('message', lib.types.String),
            ]

Yay.bind(lib)

Yay.add_generic_method('replace', ('T',), None, ['T'])

yay = Yay.new_withMessage('Hello there!')
print yay.contents.message.value

yay.replace(lib.types.String('Ciao there!'))
print yay.contents.message.value
