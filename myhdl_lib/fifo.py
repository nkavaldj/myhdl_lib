from myhdl import *
from mem   import ram_sdp_ar



def fifo(rst, clk, full, we, din, empty, re, dout, afull=None, aempty=None, afull_th=None, aempty_th=None, ovf=None, udf=None, count=None, count_max=None, depth=None, width=None):
    """ Synchronous FIFO

        Input  interface: full,  we, din
        Output interface: empty, re, dout

        Extra interface:
        afull     (o) - almost full flag, asserted when the number of empty cells <= afull_th
        aempty    (o) - almost empty flag, asserted when the number of full cells <= aempty_th

        afull_th  (i) - almost full threshold, in terms of fifo cells; signal or constant; Optional, default depth/2
        aempty_th (i) - almost empty threshold, in terms of fifo cells; signal or constant; Optional, default depth/2

        count     (o) - number of occupied fifo cells

        count_max (o) - max number of occupied fifo cells reached since the last reset
        ovf       (o) - overflow flag, set at the first write in a full fifo, cleared at reset
        udf       (o) - underflow flag, set at the first read from an empty fifo, cleared at reset
    """

    if (width == None):
        width = len(din)
    if (depth == None):
        depth = 2

    full_flg        = Signal(bool(1))
    empty_flg       = Signal(bool(1))
    we_safe         = Signal(bool(0))
    re_safe         = Signal(bool(0))

    rd_ptr          = Signal(intbv(0, min=0, max=depth))
    rd_ptr_new      = Signal(intbv(0, min=0, max=depth))
    wr_ptr          = Signal(intbv(0, min=0, max=depth))
    wr_ptr_new      = Signal(intbv(0, min=0, max=depth))

    @always_comb
    def safe_read_write():
        full.next       = full_flg
        empty.next      = empty_flg
        we_safe.next    = we and not full_flg
        re_safe.next    = re and not empty_flg


    #===========================================================================
    # Write, Read, Full, Empty
    #===========================================================================
    @always_comb
    def ptrs_new():
        rd_ptr_new.next     = ((rd_ptr + 1) % depth)
        wr_ptr_new.next     = ((wr_ptr + 1) % depth)

    @always(clk.posedge)
    def state_main():
        if (rst):
            wr_ptr.next     = 0
            rd_ptr.next     = 0
            full_flg.next   = 0
            empty_flg.next  = 1
        else:
            # Write pointer
            if (we_safe): wr_ptr.next = wr_ptr_new
            # Read pointer
            if (re_safe): rd_ptr.next = rd_ptr_new
            # Empty flag
            if (we_safe):
                empty_flg.next  = 0
            elif (re_safe and (rd_ptr_new == wr_ptr)):
                empty_flg.next  = 1
            # Full flag
            if (re_safe):
                full_flg.next   = 0
            elif (we_safe and (wr_ptr_new == rd_ptr)):
                full_flg.next   = 1


    #===========================================================================
    # Count, CountMax
    #===========================================================================
    ''' Count '''
    if (count != None) or (count_max != None) or (afull != None) or (aempty != None):
        if (count == None):
            count = Signal(intbv(0, min=0, max=depth+1))
        assert count.max > depth

        count_new  = Signal(intbv(0, min=-1, max=depth+2))

        @always_comb
        def count_comb():
            if   (we_safe and not re_safe):
                    count_new.next = count + 1
            elif (not we_safe and re_safe):
                    count_new.next = count - 1
            else:
                    count_new.next = count

        @always(clk.posedge)
        def count_proc():
            if (rst):
                count.next = 0
            else:
                count.next = count_new

    ''' Count max '''
    if (count_max != None):
        assert count_max.max > depth
        @always(clk.posedge)
        def count_max_proc():
            if (rst):
                count_max.next = 0
            else:
                if (count_max < count_new):
                    count_max.next = count_new


    #===========================================================================
    # AlmostFull, AlmostEmpty
    #===========================================================================
    ''' AlmostFull flag '''
    if (afull != None):
        if (afull_th == None):
            afull_th = depth//2
        @always(clk.posedge)
        def afull_proc():
            if (rst):
                afull.next = 0
            else:
                afull.next = (count_new >= depth-afull_th)

    ''' AlmostEmpty flag '''
    if (aempty != None):
        if (aempty_th == None):
            aempty_th = depth//2
        @always(clk.posedge)
        def aempty_proc():
            if (rst):
                aempty.next = 1
            else:
                aempty.next = (count_new <=  aempty_th)


    #===========================================================================
    # Overflow, Underflow
    #===========================================================================
    ''' Overflow flag '''
    if (ovf != None):
        @always(clk.posedge)
        def ovf_proc():
            if (rst):
                ovf.next = 0
            else:
                if (we and full_flg ):
                    ovf.next = 1

    ''' Underflow flag '''
    if (udf != None):
        @always(clk.posedge)
        def udf_proc():
            if (rst):
                udf.next = 0
            else:
                if (re and empty_flg):
                    udf.next = 1


    #===========================================================================
    # Memory instance
    #===========================================================================
    mem_we      = Signal(bool(0))
    mem_addrw   = Signal(intbv(0, min=0, max=depth))
    mem_addrr   = Signal(intbv(0, min=0, max=depth))
    mem_di      = Signal(intbv(0)[width:0])
    mem_do      = Signal(intbv(0)[width:0])

    # RAM: Simple-Dual-Port, Asynchronous read
    mem = ram_sdp_ar(   clk     = clk,
                        we      = mem_we,
                        addrw   = mem_addrw,
                        addrr   = mem_addrr,
                        di      = mem_di,
                        do      = mem_do )

    @always_comb
    def mem_connect():
        mem_we.next         = we_safe
        mem_addrw.next      = wr_ptr
        mem_addrr.next      = rd_ptr
        mem_di.next         = din
        dout.next           = mem_do

    return instances()



def convert(depth=256, width=8):
    rst, clk   = [Signal(bool(0)) for _ in range(2)]
    din, dout  = [Signal(intbv(0)[width:]) for _ in range(2)]

    re, we, empty, full, afull, aempty = [Signal(bool(0)) for _ in range(6)]
    count       = Signal(intbv(0, min=0, max=depth+1))
    count_max   = Signal(intbv(0, min=0, max=depth+1))
    afull_th    = Signal(intbv(0, min=0, max=depth+1))
    aempty_th   = Signal(intbv(0, min=0, max=depth+1))
    ovf         = Signal(bool(0))
    udf         = Signal(bool(0))

    toVerilog(fifo, rst, clk, we, din, full, re, dout, empty, afull, aempty, count, afull_th, aempty_th, ovf, udf, count_max, depth=depth, width=width)



if __name__ == "__main__":
    convert()
