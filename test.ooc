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
    }
}

operator +(one, two: Yay) -> Yay {
    Yay new("Hey, that's the result of two added Yays!")
}
