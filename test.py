import pyooc

lib = pyooc.Library('./libtest.so')

class Yay(pyooc.Class):
    _fields_ = [
            ('message', lib.types.String),
            ]
    _methods_ = [
            ('greet', None, None)
            ]
    _constructors_ = [
            ('', None),
            ('withMessage', [lib.types.String]),
            ]

Yay.bind(lib)

with_ = Yay.new_withMessage("Huhu!")
with_.greet()

without = Yay.new()
without.greet()

print 'I got the message:', with_.contents.message.value

lib.types.String.add_method('println')
with_.contents.message.println()

lib.add_operator('+', Yay, [Yay, Yay])
lib.add_operator('+=', None, [Yay, Yay])
lib.add_operator('==', lib.types.Bool, [Yay, Yay])

print (with_ + without).contents.message.value
with_ += without
with_.contents.message.println()

print (with_ == without)
print (without == without)
print (with_ != without)

krababbel = lib.generic_function('krababbel', ['T'], None, ['T'])
print krababbel(lib.types.String('yayyyyyy'))
