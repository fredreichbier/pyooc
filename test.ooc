Greeter: class {
    msg: String

    init: func (=msg) {}
    greet: func {
        "Hello %s!" format(msg) println()
    }
}
