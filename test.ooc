Greeter: class {
    msg: String
    static1337: static Int = 1337

    init: func (=msg) {}
    greet: func {
        "Hello %s!" format(msg) println()
    }
}

BetterGreeter: class extends Greeter {
    count: Int
    anotherStatic666: static Int = 666

    greet: func {
        "Hello %s (%d)!" format(msg, count) println()
    }

    init: func ~better (=msg, =count) { super(msg) }
}

AnotherCell: class <T> {
    value: T

    getValue: func -> T { value }
    setValue: func (=value) {}

    init: func (=value) {}
}

"Hell yeah! I was called! %d %d" format(Greeter static1337, BetterGreeter anotherStatic666) println()
