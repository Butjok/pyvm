import re
from struct import pack, unpack_from

from colorama import Fore
from colorama import Style

from utils import indent


class Bytecode:
    @staticmethod
    def parse_text(m): raise RuntimeError('not implemented yet')
    @staticmethod
    def parse_bytecode(code, pos): raise RuntimeError('not implemented yet')


class Int(Bytecode):
    def __init__(self, val): self.val = val

    re = r'-?\d+'
    @staticmethod
    def parse_text(m): return Int(int(m.group()))
    def __str__(self): return str(self.val)

    code = b'I'
    @staticmethod
    def parse_bytecode(code, pos): return Int(unpack_from('i', code, pos)), pos + 4
    def __bytes__(self): return pack('i', self.val)


class Str(Bytecode):
    def __init__(self, val): self.val = val

    re = r"'([^'\\]|\\.)*'"
    @staticmethod
    def parse_text(m): return Str(re.sub(r'\\(.)', r'\g<1>', m.group()[1:-1]))
    def __str__(self): return "'%s'" % re.sub(r"['\\]", r'\\\g<0>', self.val)

    code = b'S'
    @staticmethod
    def parse_bytecode(code, pos):
        # TODO: MAY NOT WORK PROPERLY
        len = unpack_from('I', code, pos)[0]
        return Str(unpack_from('%ds' % len, code, pos + 4)), pos + 4 + len
    def __bytes__(self): return pack('Is', len(self.val), self.val)


class Let(Bytecode):
    def __init__(self, varname): self.varname = varname

    re = r'let\s+(\w+)'
    @staticmethod
    def parse_text(m): return Let(m.group(1))
    def __str__(self): return 'let %s' % self.varname

    code = b'l'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.varname), self.varname)


class Get(Bytecode):
    def __init__(self, varname): self.varname = varname

    re = r'\$(\w+)'
    @staticmethod
    def parse_text(m): return Get(m.group(1))
    def __str__(self): return '$%s' % self.varname

    code = b'g'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.varname), self.varname)


class Set(Bytecode):
    def __init__(self, varname): self.varname = varname

    re = r'->(\w+)'
    @staticmethod
    def parse_text(m): return Set(m.group(1))
    def __str__(self): return '->%s' % self.varname

    code = b's'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.varname), self.varname)


class Call(Bytecode):
    def __init__(self, argn, tcall):
        self.tcall = tcall
        self.argn = argn

    re = r'\(\s*(\d*)\s*\)\s*(!?)'
    @staticmethod
    def parse_text(m): return Call(int(m.group(1)) if m.group(1) else 0, m.group(2) == '!')
    def __str__(self): return '(%s)%s' % (self.argn if self.argn else '', '!' if self.tcall else '')

    code = b'c'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('B?', self.argn, self.tcall)


class Fn(Bytecode):
    def __init__(self, label): self.label = label

    re = r'fn\s+(\w+)'
    @staticmethod
    def parse_text(m): return Fn(m.group(1))
    def __str__(self): return 'fn %s' % self.label

    code = b'f'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.label), self.label)


class Goto(Bytecode):
    def __init__(self, label): self.label = label

    re = r'goto\s+(\w+)'
    @staticmethod
    def parse_text(m): return Goto(m.group(1))
    def __str__(self): return 'goto %s' % self.label

    code = b'j'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.label), self.label)


class Jmpf(Bytecode):
    def __init__(self, label): self.label = label

    re = r'jmpf\s+(\w+)'
    @staticmethod
    def parse_text(m): return Jmpf(m.group(1))
    def __str__(self): return 'jmpf %s' % self.label

    code = b'J'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.label), self.label)


class Label(Bytecode):
    def __init__(self, name): self.name = name

    re = r'\.(\w+)'
    @staticmethod
    def parse_text(m): return Label(m.group(1))
    def __str__(self): return '.%s' % self.name

    code = b'L'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('Bs', len(self.name), self.name)


class Args(Bytecode):
    def __init__(self, names): self.names = names

    re = r'args\s+(\w+(\s*,\s*\w+)*)'
    @staticmethod
    def parse_text(m): return Args(re.split(r'\s*,\s*', m.group(1)))
    def __str__(self): return 'args %s' % ', '.join(self.names)

    code = b'a'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return pack('B', len(self.names)) + b''.join(map(lambda name: pack('Bs', len(name), name), self.names))


class Ret(Bytecode):
    re = r'ret'
    @staticmethod
    def parse_text(m): return Ret()
    def __str__(self): return 'ret'

    code = b'r'
    @staticmethod
    def parse_bytecode(code, pos): pass
    def __bytes__(self): return b''


ORDER = (Int, Str, Let, Get, Set, Call, Fn, Goto, Jmpf, Label, Args, Ret)


def parse_text(text,
               compiled=[(re.compile(t.re), t) for t in ORDER],
               ignore=re.compile(r'\s+|;[^\n]*')):
    pos = 0
    while pos < len(text):
        match = ignore.match(text, pos)
        if match:
            pos = match.end()
            continue
        for regex, t in compiled:
            match = regex.match(text, pos)
            if match:
                yield t.parse_text(match)
                pos = match.end()
                break
        else:
            raise RuntimeError(text[pos:pos+50])


def parse_bytecode(code,
                   codes=[(t.code, t) for t in ORDER]):
    pos = 0
    while pos < len(code):
        for byte, t in codes:
            if code[pos] == byte:

                pass
        else:
            raise RuntimeError(pos)


COLORS = {
    Int: Fore.CYAN,
    Str: Fore.RED,
    Let: Fore.BLUE,
    Get: Fore.BLUE,
    Set: Fore.BLUE,
    Ret: Fore.YELLOW,
    Goto: Fore.YELLOW,
    Jmpf: Fore.YELLOW,
    Fn: Fore.MAGENTA,
    Args: Fore.GREEN,
}
IN_NEWLINE = (Goto, Jmpf, Ret, Label, Set, Let)
ADD_NEWLINE = (Call, Set, Let, Ret, Goto, Jmpf, Args, Label)
NO_INDENT = (Label,)


def text(code, colored=True):
    nls = 1
    out = ''
    for cmd in code:
        if isinstance(cmd, IN_NEWLINE) and not nls:
            out += '\n'
            nls += 1

        if nls and not isinstance(cmd, NO_INDENT):
            out += indent('')

        color = COLORS[type(cmd)] if isinstance(cmd, tuple(COLORS.keys())) else None
        if colored and color:
            out += color
        out += str(cmd) + ' '
        if colored and color:
            out += Style.RESET_ALL

        nls = 0

        if isinstance(cmd, ADD_NEWLINE):
            out += '\n'
            nls += 1

    return out.rstrip()
