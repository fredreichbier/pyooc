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

    replace: func <T> (newMessage: T) {
        message = newMessage as String
    }
}
