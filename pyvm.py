from pprint import pformat
import bc
from utils import indent


PARENT = None


class VM:
    def __init__(self, code):
        self.code = code
        self.pc = 0
        self.stack = []
        self.fstack = []
        self.env = {}
        self.labels = {cmd.name: index for index, cmd in enumerate(code) if isinstance(cmd, bc.Label)}

    def run(self, env):
        try:

            self.env = env
            while self.pc < len(self.code):
                cmd = self.code[self.pc]

                if isinstance(cmd, bc.Label):
                    pass

                elif isinstance(cmd, (bc.Int, bc.Str)):
                    self.push(cmd.val)

                elif isinstance(cmd, bc.Fn):
                    self.push(Closure(self.labels[cmd.label], env))

                elif isinstance(cmd, bc.Let):
                    if cmd.varname in self.env:
                        raise VMError(cmd)
                    self.env[cmd.varname] = self.pop()[0]

                elif isinstance(cmd, (bc.Get, bc.Set)):
                    e = self.env
                    while cmd.varname not in e:
                        if PARENT not in e:
                            raise VMError(cmd)
                        e = e[PARENT]
                    if isinstance(cmd, bc.Set):
                        e[cmd.varname] = self.pop()[0]
                    elif isinstance(cmd, bc.Get):
                        self.push(e[cmd.varname])

                elif isinstance(cmd, bc.Call):
                    fn = self.pop()[0]
                    if isinstance(fn, Closure):
                        if cmd.argn:
                            self.stack.append(self.pop(cmd.argn))
                        if not cmd.tcall:
                            self.fstack.append((self.pc, self.env))
                        self.pc = fn.pc
                        env = {'': fn.env}
                    elif hasattr(fn, '__call__'):
                        fn(*([self] + self.pop(cmd.argn)))
                    else:
                        raise VMError(cmd)

                elif isinstance(cmd, bc.Args):
                    vals = self.pop()[0]
                    if len(cmd.names) != len(vals):
                        raise VMError(cmd, vals)
                    env.update(dict(zip(cmd.names, vals)))

                elif isinstance(cmd, bc.Ret):
                    if not self.fstack:
                        break
                    self.pc, env = self.fstack.pop()

                elif isinstance(cmd, bc.Goto):
                    self.pc = self.label(cmd.label)

                elif isinstance(cmd, bc.Jmpf):
                    if not self.pop()[0]:
                        self.pc = self.label(cmd.label)

                self.pc += 1

        except VMError as e:
            self.err(e.args)

    def label(self, label):
        if label not in self.labels:
            raise VMError('label', label)
        return self.labels[label]

    def push(self, *args):
        self.stack += args

    def pop(self, n=1):
        if n <= 0:
            return []
        if len(self.stack) < n:
            raise VMError('pop', n)
        top = self.stack[-n:]
        self.stack[-n:] = []
        return top

    def err(self, args):
        print('RUNTIME ERROR')
        print(indent('\n'.join(map(str, args))))
        print('NEAR')
        print(indent(bc.text(self.code[self.pc:self.pc + 5])))
        print('STACK')
        if self.stack:
            print(indent('\n'.join(map(str, reversed(self.stack)))))
        else:
            print(indent('* empty *'))
        print('ENVIRONMENT')
        env = self.env.copy()
        if PARENT in env:
            env.pop(PARENT, None)
            env['*parent*'] = '{...}'
        print(indent(pformat(env)))


class VMError(RuntimeError):
    pass


class Closure:
    def __init__(self, pc, env):
        self.pc = pc
        self.env = env