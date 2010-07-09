Greeter: class {
    msg: String

    init: func (=msg) {}
    greet: func {
        "Hello %s!" format(msg) println()
    }
}

AnotherCell: class <T> {
    value: T

    getValue: func -> T { value }
    setValue: func (=value) {}

    init: func (=value) {}
}

"Hell yeah! I was called!" println()
