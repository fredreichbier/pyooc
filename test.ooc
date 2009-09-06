import lang.String

Yay: class {
    message: String

    init: func ~withMessage (message: String) {
        this message = message
    }

    init: func {
        this message = "Hello World!"
    }

    greet: func {
        message println()
        u: String
        u = krababbel("yay")
        u println()
    }
}

operator + (one, two: Yay) -> Yay {
    Yay new("Hey, that's the result of two added Yays!")
}

operator += (one, two: Yay) {
    one message = "HA-HA!"
}

operator == (one, two: Yay) -> Bool {
    one message == two message
}

operator != (one, two: Yay) -> Bool {
    one message != two message
}

krababbel: func <T> (hey: T) -> T {
    (hey as String) println()
    return hey
}
