Greeter: class {
    msg: String
    static1337: static Int = 1337

    init: func (=msg) {
        mimi = "no"
    }
    greet: func {
        "Hello %s!" format(msg toCString()) println()
    }

    helloWorld: func <T> (v: T) {
        T name println()
    }

    mimi: String {
        set(=mimi) {
            "Setter invoked! %s" format(mimi toCString()) println()
        }
        get {
            "Getter invoked!" println()
            mimi
        }
    }

    staticMimi: static String {
        set(=staticMimi) {
            "STATIC Setter invoked! %s" format(staticMimi toCString()) println()
        }
        get {
            "STATIC Getter invoked!" println()
            staticMimi
        }
   }
}

BetterGreeter: class extends Greeter {
    count: Int
    anotherStatic666: static Int = 666

    greet: func {
        "Hello %s (%d)!" format(msg toCString(), count) println()
    }

    gimme: func (a, b, c: String) -> (Int, Int) {
        (count, anotherStatic666)
    }

    gimmeGeneric: func <T> (v: T) -> (T, T) {
        (v, v)
    }

    init: func ~better (=msg, =count) { super(msg) }
}

AnotherCell: class <T> {
    value: T

    getValue: func -> T { value }
    setValue: func (=value) {}

    getSomeStuff: func -> (T, T) {
        (value, value)
    }

    fooBar: func <U> (u: U) -> (U) {
        (U)
    }
    
    moo: func <U> (U: Class) -> (Int, U, Int) {
        U name println()
        (1, "Urgh", 3)
    }

    init: func (=value) {}

}

yayx0r: func -> String {
    "yayX0R" println()
    ":-)"
}

someGlobalVariable: String = "<3"

"Hell yeah! I was called! %d %d" format(Greeter static1337, BetterGreeter anotherStatic666) println()

Greeter staticMimi = "I'm sad."

testCallback: func (callMe: Func (String) -> Int) -> Int {
    "%d = 5" format(callMe("Hello from the ooc world!")) println()
    1337556
}
