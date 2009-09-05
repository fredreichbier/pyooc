import lang.String

Yay: class {
    hello: func {
        "Hello World!" println()
    }
}

doIt: func -> Yay {
    return Yay new()
}
