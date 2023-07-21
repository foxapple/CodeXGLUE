EOF = -1

class Lexer(object):
    def __init__(self, in_unicode):
        self.input = in_unicode
        self.index = 0
        self.c = self.input[self.index]

    def consume(self):
        self.index += 1
        if self.index >= len(self.input):
            self.c = EOF
        else:
            self.c = self.input[self.index]


class CommandLexer(Lexer):
    # todo: describe grammar more formally
    """
    cmd : NAME (option string?)*
    option: -NAME | [^"']+ | NUM
    string : (["']) .* \1
    NAME : [a-zA-Z]+
    NUM : 0-9+
    """

    _white_space = ' \t'

    def __init__(self, in_unicode):
        Lexer.__init__(self, in_unicode)

    def look_ahead(self, s):
        if self.index + len(s) >= len(self.input):
            return False
        return self.input[self.index:(self.index + len(s))] == s

    def _WHITE_SPACE(self):
        while self.c in self._white_space:
            self.consume()

    def _NAME(self):
        name_buf = []
        while self.c != EOF and self.c.isalpha():
            name_buf.append(self.c)
            self.consume()
        return ''.join(name_buf)

    def _OPTION(self):
        opt_buf = []
        while self.c != EOF and self.c == '-':
            opt_buf.append(self.c)
            self.consume()
        if self.c == EOF:
            SyntaxError("expected option name, got nothing")
        opt_buf.append(self._NAME())
        return ''.join(opt_buf)

    def _LONG_OPTION(self):
        opt_buf = []
        while self.c != EOF and self.c == '-':
            opt_buf.append(self.c)
            self.consume()
        if self.c == EOF:
            SyntaxError("expected option name, got nothing")
        while self.c != EOF and (self.c.isalpha() or self.c == '-'):
            opt_buf.append(self.c)
            self.consume()
        return ''.join(opt_buf)

    def _VALUE(self):
        val_buf = []
        while self.c != EOF and self.c not in self._white_space:
            val_buf.append(self.c)
            self.consume()
        return ''.join(val_buf)

    def _STRING(self):
        delimiter = self.c
        str_buf = []
        self.consume()
        while self.c != EOF:
            if self.c == '\\':
                self.consume()
                if self.c == delimiter:
                    str_buf.append(self.c)
                    self.consume()
                else:
                    str_buf.append('\\')
                    str_buf.append(self.c)
                    self.consume()
            else:
                str_buf.append(self.c)
                self.consume()
            if self.c == delimiter:
                self.consume()
                break
        return ''.join(str_buf)

    def __iter__(self):
        if self.c in self._white_space:
            self._WHITE_SPACE()
        if self.c.isalpha():
            yield self._NAME()
        else:
            SyntaxError("cannot find command name")

        while self.c != EOF:
            if self.c in self._white_space:
                self._WHITE_SPACE()
            elif self.look_ahead('--'):
                yield self._LONG_OPTION()
            elif self.c == '-':
                yield self._OPTION()
            elif self.c in '\'"':
                yield self._STRING()
            else:
                # For example, eats locate *pat* and log -l5
                yield self._VALUE()
        raise StopIteration
