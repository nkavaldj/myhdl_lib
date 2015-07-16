from myhdl import *


def mux(sel, ls_di, do):
    """ Multiplexes a list of input signals to an output signal
            do = sl_di[sel]

            sel - select index
            ls_di - list of input signals
            do - output signals
            
    """
    N = len(ls_di)
    @always_comb
    def _mux():
        do.next = 0
        for i in range(N):
            if i == sel:
                do.next = ls_di[i]
    return _mux


def demux(sel, di, ls_do):
    """ Demultiplexes an input signal to a list of output signals
            ls_do[sel] =  di

            sel - select index
            di - input signal
            ls_do - list of output signals
    """
    N = len(ls_do)
    @always_comb
    def _demux():
        for i in range(N):
            ls_do[i].next = 0
            if i == sel:
                ls_do[i].next = di
    return _demux


def ls_mux(sel, lsls_di, ls_do):
    """ Multiplexes a list of input signal structures to an output structure. 
        A structure is represented by a list of signals: [signal_1, signal_2, ..., signal_n]
            ls_do[0] = lsls_di[sel][0]
            ls_do[1] = lsls_di[sel][1]
            ...
            ls_do[n] = lsls_di[sel][n]

            sel - select index
            lsls_di - list of input signal structures: [[sig, sig, ..., sig], [sig, sig, ..., sig], ..., [sig, sig, ..., sig]]
            ls_do - output signal structure: [sig, sig, ..., sig]
    """
    N = len(ls_do)
    lsls_in = [list(x) for x in zip(*lsls_di)]
    return [mux(sel, lsls_in[i], ls_do[i]) for i in range(N)]


def ls_demux(sel, ls_di, lsls_do):
    """ Demultiplexes an input signal structure to list of output structures. 
        A structure is represented by a list of signals: [signal_1, signal_2, ..., signal_n]
            lsls_do[sel][0] = ls_di[0]
            lsls_do[sel][1] = ls_di[1]
            ...
            lsls_do[sel][n] = ls_di[n]

            sel - select index
            ls_di - input signal structure: [sig, sig, ..., sig]
            lsls_do - list of output signal structures: [[sig, sig, ..., sig], [sig, sig, ..., sig], ..., [sig, sig, ..., sig]]
    """
    N = len (ls_di)
    lsls_out = [list(x) for x in zip(*lsls_do)]
    return [demux(sel, ls_di[i], lsls_out[i])for i in range(N)]


def bitslice_select(offset, bv_di, bv_do):
    ''' Selects a bit-slice from a bit-vector
            offset - (i) bit offset of the slice
            bv_di  - (i) bit vector where the slice is taken from
            bv_do  - (o) selected slice; the length of this bit-vector defines the number of bit in the slice

            bv_do = bv_di[len(bv_do)+offset:offset]
    '''
    LEN_I = len(bv_di)
    LEN_O = len(bv_do)

    assert LEN_I >= LEN_O, "bitslice_select: expects len(bv_di) >= len(bv_do), but len(bv_di)={}, len(bv_do)".format(LEN_I, LEN_O)

    OFFSET_MAX = LEN_I - LEN_O + 1

    @always_comb
    def _slice():
        bv_do.next = 0
        for i in range(OFFSET_MAX):
            if i==offset:
                for b in range(LEN_O):
                    bv_do.next[b] = bv_di[i+b]

    return _slice


def byteslice_select(offset, bv_di, bv_do):
    ''' Selects a slice of length 8*n aligned on a byte from a bit-vector
            offset - (i) byte offset of the slice
            bv_di  - (i) bit vector where the slice is taken from; must len(bv_di) = 8*m
            bv_do  - (o) selected slice; must len(bv_do) = 8*n, n<=m; len(bv_do) defines the number of bit in the slice
    '''
    LEN_I = len(bv_di)
    LEN_O = len(bv_do)

    assert (LEN_I % 8)==0, "byteslice_select: expects len(bv_di)=8*x, but len(bv_di)={} bits".format(LEN_I)
    assert (LEN_O % 8)==0, "byteslice_select: expects len(bv_do)=8*x, but len(bv_do)={} bits".format(LEN_O)

    bit_offset = Signal(intbv(0)[len(offset)+3:])

    @always_comb
    def _offset():
        bit_offset.next = offset << 3

    _slice = bitslice_select(bit_offset, bv_di, bv_do)

    return _offset, _slice

if __name__ == '__main__':
    pass