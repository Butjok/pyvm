import lisp
import bc
import pyvm
from utils import indent


def main():

    with open('test.lisp') as f:
        code = lisp.parse(lisp.sexp(lisp.lex('(do %s\n)' % f.read())))
        print('LISP')
        print(indent(str(code)))

        code = [bc.Goto('main')] + lisp.add_lists(map(lambda fn: fn.compile_body(), code.fns())) + [
            bc.Label('main')] + code.compile() + [bc.Ret()]

        print('BYTECODE')
        print(indent(bc.text(code)))

        vm = pyvm.VM(code)
        vm.run({
            'print': lambda v, *args: print(*args)
        })


if __name__ == '__main__':
    main()