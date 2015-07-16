from myhdl import *


def assign(a,b):
    ''' Combinatorial assignment: a = b '''
    @always_comb
    def _assign():
        a.next = b
    return _assign


def byteorder(bv_di, bv_do, REVERSE=True):
    """ Reverses the byte order of an input bit-vector
            bv_di - (i) input bit-vector
            bv_do - (o) output bit-vector
    """
    BITS  = len(bv_di)

    assert (BITS % 8)==0, "byteorder: expects len(bv_in)=8*x, but len(bv_in)={}".format(BITS)

    if REVERSE:
        BYTES = BITS//8
        y = ConcatSignal(*[bv_di(8*(b+1),8*b) for b in range(BYTES)])

        @always_comb
        def _reverse():
            bv_do.next = y

    else:
        @always_comb
        def _pass():
            bv_do.next = bv_di

    return instances()


if __name__ == '__main__':
    pass