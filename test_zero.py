from pyooc.ffi import Library
from pyooc.parser import Repository
from pyooc.bind import bind_module

lib = Library('./libtest.so')

repo = Repository('repo')

bind_module(lib, repo, 'test')
test = lib.get_module('test')

g = test.Greeter.new('Mr Banana')
g.helloWorld('huhu')
g.greet()

b = test.BetterGreeter.new_better('Mr Sausage', 42)
b.greet()
print b.contents.msg.value
print b.contents.count.value

print g.class_().contents.static1337.value
print b.class_().contents.anotherStatic666.value

print tuple(i.value for i in b.gimmeGeneric(123, restype0=lib.types.Int, restype1=lib.types.Int))
print tuple(i.value for i in b.gimme('1', '2', '3'))

cell = test.AnotherCell.new('heya')
print cell.getValue().value
print cell.getSomeStuff()[0].value
s = cell.moo(lib.types.String.class_(), restype1=lib.types.String)[1]
print s.value

print test.yayx0r().value

print test.someGlobalVariable.value
test.someGlobalVariable.value = "<5"
print test.someGlobalVariable.value

print g.contents.mimi.value
g.contents.mimi = 'HELLO WORLD'
print g.contents.mimi.value

print g.class_().contents.staticMimi.value
g.class_().contents.staticMimi = 'HECK I\'M SO HAPPY'
print g.class_().contents.staticMimi.value

def callback(greet):
    print 'greet received:', greet.value
    return 5

print test.testCallback(lib.types.Closure.from_func(callback, lib.types.Int, (lib.types.String,))).value
