from myhdl import *
from mem import ram_sdp_ar



def fifo_speculative(rst, clk, full, we, din, empty, re, dout, wr_commit=None, wr_discard=None, rd_commit=None, rd_discard=None, afull=None, aempty=None, count=None, afull_th=None, aempty_th=None, ovf=None, udf=None, count_max=None,  depth=None, width=None):
    """ Speculative FIFO

        Input  interface: full,  we, din,  wr_commit, wr_discard
        Output interface: empty, re, dout, rd_commit, rd_discard

        we         (i) - writes data speculatively (the data can be later removed from the fifo)
        wr_commit  (i) - accept the speculatively written data (can be read)
        wr_discard (i) - remove the speculatively written data at once
        full       (o) - asserted when there are no empty cells to write data speculatively

        If we is asserted together with the wr_commit or wr_discard, the data being written is affected by the commit/discard command.
        If wr_commit and wr_discard are asserted simultaneously, the wr_discard wins.

        re         (i) - reads data speculatively (the data can be later restored)
        rd_commit  (i) - removes the speculatively read data at once
        rd_discard (i) - restores the speculatively read data (will be read again)
        empty      (o) - asserted when there are no committed date to be read

        If re is asserted together with the rd_commit or rd_discards, the data being read is affected by the commit/discard command.
        If rd_commit and rd_discard are asserted simultaneously, the rd_discard wins.

        Note: This fifo can be Full and Empty at the same time - all fifo cells are occupied by data that are either speculatively written or speculatively read

        Extra interface:
        afull      (o) - almost full flag, asserted when the number of empty cells <= afull_th
        aempty     (o) - almost empty flag, asserted when the number of full cells <= aempty_th

        afull_th   (i) - almost full threshold, in terms of fifo cells; Optional, default depth/2
        aempty_th  (i) - almost empty threshold, in terms of fifo cells; Optional, default depth/2

        count      (o) - number of occupied fifo cells, committed and not committed (speculatively written/read)
        count_max  (o) - max number of occupied fifo cells reached since the last reset
        ovf        (o) - overflow flag, set at the first write in a full fifo, cleared at reset
        udf        (o) - underflow flag, set at the first read from an empty fifo, cleared at reset
    """

    if (width == None):
        width = len(din)
    if (depth == None):
        depth = 2

    assert ((wr_commit != None) and (wr_discard != None)) or ((wr_commit == None) and (wr_discard == None)), "SFIFO ERROR: Interface signals wr_commit and wr_discard must be either both used or both left unused"
    assert ((rd_commit != None) and (rd_discard != None)) or ((rd_commit == None) and (rd_discard == None)), "SFIFO ERROR: Interface signals rd_commit and rd_discard must be either both used or both left unused"

    wr_commit       = wr_commit  if (wr_commit  != None) else Signal(bool(1))
    wr_discard      = wr_discard if (wr_discard != None) else Signal(bool(0))
    rd_commit       = rd_commit  if (rd_commit  != None) else Signal(bool(1))
    rd_discard      = rd_discard if (rd_discard != None) else Signal(bool(0))

    full_flg        = Signal(bool(1))
    empty_flg       = Signal(bool(1))
    we_safe         = Signal(bool(0))
    re_safe         = Signal(bool(0))
    swr_non0        = Signal(bool(0))
    srd_non0        = Signal(bool(0))
    wr_commit_non0  = Signal(bool(0))
    rd_commit_non0  = Signal(bool(0))
    wr_discard_non0 = Signal(bool(0))
    rd_discard_non0 = Signal(bool(0))

    # Almost full/empty and their thresholds
    afull_flg       = Signal(bool(0))
    aempty_flg      = Signal(bool(0))
    if (afull_th == None):
        afull_th = depth//2
    if (aempty_th == None):
        aempty_th = depth//2

    afull           = afull  if (afull  != None) else Signal(bool(0))
    aempty          = aempty if (aempty != None) else Signal(bool(0))
    count           = count  if (count  != None) else Signal(intbv(0, min=0, max=depth + 1))

    ovf             = ovf       if (ovf       != None) else Signal(bool(0))
    udf             = udf       if (udf       != None) else Signal(bool(0))
    count_max       = count_max if (count_max != None) else Signal(intbv(0, min=0, max=depth+1))

    rd_ptr          = Signal(intbv(0, min=0, max=depth))
    wr_ptr          = Signal(intbv(0, min=0, max=depth))
    srd_ptr         = Signal(intbv(0, min=0, max=depth))
    srd_ptr_new     = Signal(intbv(0, min=0, max=depth))
    swr_ptr         = Signal(intbv(0, min=0, max=depth))
    swr_ptr_new     = Signal(intbv(0, min=0, max=depth))

    # Data written in the fifo (committed and not committed)
    data_count      = Signal(intbv(0, min=0,   max=depth + 1))
    data_count_max  = Signal(intbv(0, min=0,   max=depth + 1))

    @always_comb
    def out_assign():
        full.next           = full_flg
        empty.next          = empty_flg
        afull.next          = afull_flg
        aempty.next         = aempty_flg
        count.next          = data_count
        count_max.next      = data_count_max

    @always_comb
    def safe_read_write():
        we_safe.next        = we and not full_flg
        re_safe.next        = re and not empty_flg

    @always_comb
    def non_zero_commits():
        wr_commit_non0.next     = wr_commit and (swr_non0 or we_safe) and not wr_discard
        rd_commit_non0.next     = rd_commit and (srd_non0 or re_safe) and not rd_discard
        #
        wr_discard_non0.next    = wr_discard and (swr_non0 or we_safe)
        rd_discard_non0.next    = rd_discard and (srd_non0 or re_safe)

    """ ---------------------------- """
    """ - Write, Read, Full, Empty - """
    """ ---------------------------- """

    @always_comb
    def sptrs_new():
        """ Next value for the speculative pointers """

        if (wr_discard):
            swr_ptr_new.next     = wr_ptr
        elif (we_safe):
            swr_ptr_new.next     = ((swr_ptr + 1) % depth)
        else:
            swr_ptr_new.next     = swr_ptr

        if (rd_discard):
            srd_ptr_new.next     = rd_ptr
        elif (re_safe):
            srd_ptr_new.next     = ((srd_ptr + 1) % depth)
        else:
            srd_ptr_new.next     = srd_ptr

    @always(clk.posedge)
    def state_main():
        if (rst):
            wr_ptr.next     = 0
            rd_ptr.next     = 0
            swr_ptr.next    = 0
            srd_ptr.next    = 0
            swr_non0.next   = 0
            srd_non0.next   = 0
            full_flg.next   = 0
            empty_flg.next  = 1
        else:

            # Speculative Write pointer
            swr_ptr.next = swr_ptr_new

            # Speculative Read pointer
            srd_ptr.next = srd_ptr_new

            # Write pointer
            if (wr_commit): wr_ptr.next = swr_ptr_new

            # Read pointer
            if (rd_commit): rd_ptr.next = srd_ptr_new

            # Empty flag
            if (wr_commit_non0 or rd_discard_non0):
                empty_flg.next  = 0
            elif (re_safe and (srd_ptr_new == wr_ptr)):
                empty_flg.next  = 1

            # Full flag
            if (rd_commit_non0 or wr_discard_non0):
                full_flg.next   = 0
            elif (we_safe and (swr_ptr_new == rd_ptr)):
                full_flg.next   = 1

            # swr_non0 flag
            if (wr_commit or wr_discard):
                swr_non0.next   = 0
            elif (we_safe):
                swr_non0.next   = 1

            # srd_non0 flag
            if (rd_commit or rd_discard):
                srd_non0.next   = 0
            elif (re_safe):
                srd_non0.next   = 1


    """
    rd                        srd            wr                        swr            rd
    ^                         ^              v                         v              ^
    |#########################|%%%%%%%%%%%%%%|*************************|..............|
    |<------ srd_count ------>|<------------>|<------ swr_count ------>|<------------>|
    |<--------------- wr_count ------------->|<--------------- rd_count ------------->|
    |<----------------------------------- depth ------------------------------------->|
    """

    """ ------------------------------------ """
    """ - Almost_Full, Almost_Empty, Count - """
    """ ------------------------------------ """
    # count of the speculatively written data
    swr_count       = Signal(intbv(0, min=0,   max=depth + 1))
    # count of the speculatively read data
    srd_count       = Signal(intbv(0, min=0,   max=depth + 1))
    # count of the write committed data
    wr_count        = Signal(intbv(0, min=0,   max=depth + 1))
    # count of the not write committed positions
    rd_count        = Signal(intbv(0, min=0,   max=depth + 1))

    @always(clk.posedge)
    def state_extra():
        if (rst):
            swr_count.next      = 0
            srd_count.next      = 0
            wr_count.next       = 0
            rd_count.next       = depth
            data_count.next     = 0
            afull_flg.next      = 0
            aempty_flg.next     = 1
            data_count_max.next = 0
        else:
            swr_count_new   = 0
            if (not wr_commit and not wr_discard):
                swr_count_new   = int((swr_count + 1) if (we_safe) else swr_count)

            swr_count.next  = swr_count_new

            srd_count_new   = 0
            if (not rd_commit and not rd_discard):
                srd_count_new   = int((srd_count + 1 if (re_safe) else srd_count))

            srd_count.next  = srd_count_new

            wr_add_new = 0
            if (wr_commit and not wr_discard):
                wr_add_new  = int((swr_count + 1) if (we_safe) else swr_count)

            rd_add_new = 0
            if (rd_commit and not rd_discard):
                rd_add_new  = int((srd_count + 1) if (re_safe) else srd_count)

            wr_count_new    = wr_count + wr_add_new - rd_add_new
            rd_count_new    = rd_count - wr_add_new + rd_add_new

            wr_count.next   = wr_count_new
            rd_count.next   = rd_count_new

            aempty_flg.next = ((wr_count_new - srd_count_new) <= aempty_th)
            afull_flg.next  = ((rd_count_new - swr_count_new) <= afull_th )

            # Count data in the fifo
            data_count_new  = wr_count_new + swr_count_new
            data_count.next = data_count_new

            if (data_count_max < data_count_new): data_count_max.next = data_count_new

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

    """ ------------------- """
    """ - Memory instance - """
    """ ------------------- """
    mem_we      = Signal(bool(0))
    mem_addrw   = Signal(intbv(0, min=0, max=depth))
    mem_addrr   = Signal(intbv(0, min=0, max=depth))
    mem_di      = Signal(intbv(0)[width:0])
    mem_do      = Signal(intbv(0)[width:0])

    # RAM: Simple-Dual-Port, Asynchronous Read
    mem = ram_sdp_ar(   clk     = clk,
                        we      = mem_we,
                        addrw   = mem_addrw,
                        addrr   = mem_addrr,
                        di      = mem_di,
                        do      = mem_do )

    @always_comb
    def mem_connect():
        mem_we.next         = we_safe
        mem_addrw.next      = swr_ptr
        mem_addrr.next      = srd_ptr
        mem_di.next         = din
        dout.next           = mem_do

    return instances()


def convert(depth=256, width=8):

    rst, clk   = [Signal(bool(0)) for _ in range(2)]
    din, dout  = [Signal(intbv(0)[width:]) for _ in range(2)]

    re, we, empty, full, afull, aempty = [Signal(bool(0)) for _ in range(6)]
    wr_commit, wr_discard, rd_commit, rd_discard = [Signal(bool(0)) for _ in range(4)]
    count       = Signal(intbv(0, min=0, max=depth+1))
    afull_th    = Signal(intbv(0, min=0, max=depth+1))
    aempty_th   = Signal(intbv(0, min=0, max=depth+1))
    ovf         = Signal(bool(0))
    udf         = Signal(bool(0))
    count_max   = Signal(intbv(0, min=0, max=depth+1))

    toVerilog(fifo_speculative, rst, clk, full, we, din, empty, re, dout, wr_commit, wr_discard, rd_commit, rd_discard, afull, aempty, count, afull_th, aempty_th, ovf, udf, count_max, depth=depth, width=width)


if __name__ == "__main__":
    convert()
