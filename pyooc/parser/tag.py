class Token(object):
    INVALID = 0
    IDENTIFIER = 1
    LPAREN = 2
    RPAREN = 3
    COMMA = 4
    END = 5

def lex(next):
    running = True

    def _shift(chars):
        char = next()
        try:
            while char in chars:
                char = next()
        except StopIteration:
            running = False
        return char

    char = next()
    while running:
        if char == '(':
            yield (Token.LPAREN, char)
            char = _shift((' ',))
        elif char == ')':
            yield (Token.RPAREN, char)
            char = _shift((' ',))
        elif char == ',':
            yield (Token.COMMA, char)
            char = _shift((' ',))
        else:
            s = ''
            try:
                while char not in '(),':
                    # include spaces, e.g. `unsigned int` contains a space
                    s += char
                    char = next()
            except StopIteration:
                running = False
            yield (Token.IDENTIFIER, s)
    yield (Token.END, '')

class ParsingError(Exception):
    pass

def _parse(next, token):
    if token[0] == Token.IDENTIFIER:
        value = token[1]
        token = next()
        if token[0] in (Token.END, Token.COMMA, Token.RPAREN):
            return (token, value)
        elif token[0] == Token.LPAREN:
            args = []
            token = next()
            while token[0] != Token.RPAREN:
                token, new_arg = _parse(next, token)
                args.append(new_arg)
                if (token[0] != Token.COMMA
                        and token[0] != Token.RPAREN):
                    raise ParsingError('Malformed argument list, unexpected token: %r' % (token,))
                if token[0] == Token.COMMA:
                    token = next()
            return (token, (value, tuple(args)))
        else:
            raise ParsingError('Unexpected token: %r' % (token,))
    else:
        raise ParsingError('Unexpected token: %r' % (token,))
            
def parse(stream):
    return _parse(stream.next, stream.next())[1]

def parse_string(s):
    return parse(lex(iter(s).next))

def translate(parsed):
    """
        translate a tuple (mod, args) to a string
    """
    if isinstance(parsed, tuple):
        return '%s(%s)' % (parsed[0], ', '.join(map(translate, parsed[1])))
    else:
        return parsed

