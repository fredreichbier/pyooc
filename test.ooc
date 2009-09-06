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

gimmeAString: func -> String {
    "I like turtles."
}
