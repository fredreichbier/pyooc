Yay: class <T, U> {
    message: T

    init: func (msg: String) {
        message = msg
    }

    printy: func {
        this message as String println()
    }
}
