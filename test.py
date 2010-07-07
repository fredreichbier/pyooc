import pyooc.ffi
import pyooc.ffi.sdk.text.Buffer

lib = pyooc.ffi.Library('./libtest.so')

test = lib.get_module('test')

buffer = pyooc.ffi.sdk.text.Buffer.bind(lib)
buf = buffer.Buffer.new()

for _ in xrange(3):
    buf.append_chr('A')

print buf.toString().value
