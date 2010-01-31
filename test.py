import pyooc
import pyooc.sdk.text.StringBuffer

lib = pyooc.Library('./libtest.so')

test = lib.get_module('test')

string_buffer = pyooc.sdk.text.StringBuffer.bind(lib)
buf = string_buffer.StringBuffer.new()

for _ in xrange(3):
    buf.write_chr('A')

print buf.toString().value
