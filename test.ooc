Greeter: class implements Comparable {
    msg: String

    init: func (=msg) {}
    greet: func {
        "Hello %s!" format(msg) println()
    }

    compareTo: func <T> (value: T) -> Int {
        0
    }
}

"Hell yeah! I was called!" println()
