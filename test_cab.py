from pyooc.bind.utils import compile_and_bind

module = compile_and_bind('''
helloWorld: func (amount: SizeT) {
    for(i in 0..amount) {
        "Hello World! (#%d)" format(i + 1) println()
    }
}
''')
module.helloWorld(1337)
