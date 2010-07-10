from pyooc.ffi import Library
from pyooc.zero import Repository
from pyooc.zero.llamaize import llamaize_module

lib = Library('./libtest.so')

repo = Repository('repo')

llamaize_module(lib, repo, 'test')
test = lib.get_module('test')

g = test.Greeter.new('Mr Banana')
g.greet()
print g.contents.msg.value

b = test.BetterGreeter.new_better('Mr Sausage', 1337)
b.greet()
print b.contents.msg.value
print b.contents.count.value
