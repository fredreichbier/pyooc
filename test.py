import pyooc

lib = pyooc.Library('./libtest.so')

krababbel = lib.generic_function('krababbel', ['T'], 'T', ['T'])
print krababbel(lib.types.String('yayyyyyy'), restype=lib.types.String).value
