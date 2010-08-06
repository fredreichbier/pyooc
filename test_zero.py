from pyooc.ffi import Library
from pyooc.parser import Repository
from pyooc.bind import bind_module

lib = Library('./libtest.so')

repo = Repository('repo')

bind_module(lib, repo, 'test')
test = lib.get_module('test')

g = test.Greeter.new('Mr Banana')
g.greet()

b = test.BetterGreeter.new_better('Mr Sausage', 1337)
b.greet()
print b.contents.msg.value
print b.contents.count.value
