import re
import bc
import itertools


#
# TODO: TAIL CALL
#


def add_lists(lists):
    return list(itertools.chain(*lists))


class Node:
    def compile(self):
        raise RuntimeError('not implemented yet')
    def fns(self):
        raise RuntimeError('not implemented yet')


class Int(Node):
    re = r'-?\d+'
    def __init__(self, m):
        self.val = int(m.group())
    def __str__(self):
        return str(self.val)
    def compile(self):
        return [bc.Int(self.val)]
    def fns(self):
        return []


class Str(Node):
    re = r"'([^'\\]|\\.)*'"
    def __init__(self, m):
        self.val = re.sub(r'\\(.)', r'\g<1>', m.group()[1:-1])
    def __str__(self):
        return "'%s'" % re.sub(r"['\\]", r'\\\g<0>', self.val)
    def compile(self):
        return [bc.Str(self.val)]
    def fns(self):
        return []


class Id(Node):
    re = r'\w+'
    def __init__(self, m):
        self.name = m.group()
    def __str__(self):
        return self.name
    def compile(self):
        return [bc.Get(self.name)]
    def fns(self):
        return []


class LParen(Node):
    re = r'\('
    def __init__(self, m):
        pass
    def __str__(self):
        return '('


class RParen(Node):
    re = r'\)'
    def __init__(self, m):
        pass
    def __str__(self):
        return ')'


LEX_ORDER = (Int, Str, Id, LParen, RParen)


def lex(text,
        compiled=[(re.compile(t.re), t) for t in LEX_ORDER],
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
                yield t(match)
                pos = match.end()
                break
        else:
            raise RuntimeError(text[pos:pos+50])


def sexp(toks):
    stack = []
    lst = []
    for tok in toks:
        if isinstance(tok, LParen):
            stack.append(lst)
            lst = []
        elif isinstance(tok, RParen):
            if not stack:
                raise RuntimeError(tok)
            prev = stack.pop()
            prev.append(lst)
            lst = prev
        else:
            lst.append(tok)
    return lst[0]


class Empty(Node):
    def compile(self):
        return []
    def fns(self):
        return []


class Do(Node):
    id = 'do'
    def __init__(self, *exps):
        self.body = list(map(parse, exps))
    def __str__(self):
        return '(do %s)' % ' '.join(map(str, self.body))
    def compile(self):
        return add_lists(map(lambda n: n.compile(), self.body))
    def fns(self):
        return add_lists(map(lambda n: n.fns(), self.body))


class When(Node):
    id = 'when'
    total = 0
    def __init__(self, cond, *then):
        self.cond = parse(cond)
        self.val = Do(*then)
        self.label = 'w%d' % When.total
        When.total += 1
    def __str__(self):
        return '(when %s %s)' % (self.cond, self.val)
    def compile(self):
        return self.cond.compile() + [bc.Jmpf(self.label)] + self.val.compile() + [bc.Label(self.label)]
    def fns(self):
        return self.cond.fns() + self.val.fns()


class Set(Node):
    id = 'set'
    def __init__(self, name, val):
        assert isinstance(name, Id)
        self.var = name
        self.val = val
    def __str__(self):
        return '(set %s %s)' % (self.var, self.val)
    def compile(self):
        return self.val.compile() + [bc.Set(self.var.name)]
    def fns(self):
        return self.val.fns()


class Fn(Node):
    id = 'fn'
    total = 0
    def __init__(self, args, *body):
        assert isinstance(args, list) and all(map(lambda a: isinstance(a, Id), args))
        self.args = args
        self.val = Do(*body)
        self.label = 'f%d' % Fn.total
        Fn.total += 1
    def __str__(self):
        return '(fn (%s) %s)' % (' '.join(map(str, self.args)), self.val)
    def compile(self):
        return [bc.Fn(self.label)]
    def compile_body(self):
        return [bc.Label(self.label), bc.Args(map(str, self.args))] + self.val.compile() + [bc.Ret()]
    def fns(self):
        return [self]


class Call(Node):
    def __init__(self, *exp):
        assert len(exp) >= 1
        self.fn = parse(exp[0])
        self.args = list(map(parse, exp[1:]))
    def __str__(self):
        return '(%s %s)' % (self.fn, ' '.join(map(str, self.args)))
    def compile(self):
        return add_lists(map(lambda n: n.compile(), self.args)) + self.fn.compile() + [bc.Call(len(self.args), False)]
    def fns(self):
        return self.fn.fns() + add_lists(map(lambda n: n.fns(), self.args))


PARSE_ORDER = (Do, When, Fn)


def parse(exp,
          ids=[(t.id, t) for t in PARSE_ORDER]):
    if not isinstance(exp, list):
        return exp
    else:
        if not exp:
            raise RuntimeError('empty form')
        for id, t in ids:
            if isinstance(exp[0], Id) and exp[0].name == id:
                return t(*exp[1:])
        return Call(*exp)

