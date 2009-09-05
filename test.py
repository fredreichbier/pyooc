import pyooc
from pyooc import types

lib = pyooc.Library('./libtest.so')
doIt = lib.doIt

class Yay(pyooc.KindOfClass):
    fields = [('a', types.Int)]

doIt.restype = Yay

Yay.bind(lib)
Yay.add_method('hello')

yay = doIt()
yay.hello()
