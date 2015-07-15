from myhdl import *


def assign(a,b):
    ''' Combinatorial assignment: a = b '''
    @always_comb
    def _assign():
        a.next = b
    return _assign


if __name__ == '__main__':
    pass