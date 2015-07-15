from myhdl import *


def arbiter(rst, clk, req_vec, sel, en, ARBITER_TYPE="priority"):
    ''' Wrapper that provides common interface to all arbiters '''
    if ARBITER_TYPE == "priority":
        _arb = arbiter_priority(req_vec, sel)
    elif (ARBITER_TYPE == "roundrobin"):
        _arb = arbiter_roundrobin(rst, clk, req_vec, sel, en)
    else:
        assert "Arbiter: Unknown arbiter type: {}".format(ARBITER_TYPE)

    return _arb


def arbiter_priority(req_vec, sel):
    """ Static priority arbiter: finds the active request with highest priority and presents its index on the sel output.
            req_vec - (i) vector of request signals, req_vec[0] is with the highest priority
            sel     - (o) the index of the request with highest priority
    """
    REQ_NUM = len(req_vec)

    @always_comb
    def prioroty_encoder():
        sel.next = 0
        for i in range(REQ_NUM):
            if ( req_vec[i]==1 ):
                sel.next = i
                break

    return instances()


def arbiter_roundrobin(rst, clk, req_vec, sel, en):
    """ Round Robin arbiter: finds the active request with highest priority and presents its index on the sel output.
            req_vec - (i) vector of request signals, priority changes dynamically 
            sel     - (o) the index of the request with highest priority
            en      - (i) update priority: currently selected req_vec[sel] gets the lowest priority, req_vec[sel+1] gets the highest priority
                        Should be activated in the clock cycle when output sel is used
    """
    REQ_NUM = len(req_vec)
    ptr = Signal(intbv(0, min=0, max=REQ_NUM))
    ptr_new = Signal(intbv(0, min=0, max=REQ_NUM))

    @always(clk.posedge)
    def ptr_proc():
        if (rst):
            ptr.next = REQ_NUM-1
        elif (en):
            ptr.next = ptr_new

    @always_comb
    def roundrobin_encoder():
        ptr_new.next = 0
        for i in range(REQ_NUM):
            if (i>ptr):
                if ( req_vec[i]==1 ):
                    ptr_new.next = i
                    return
        for i in range(REQ_NUM):
            if ( req_vec[i]==1 ):
                ptr_new.next = i
                return

    @always_comb
    def _out():
        sel.next = ptr_new


    return instances()


if __name__ == '__main__':
    pass