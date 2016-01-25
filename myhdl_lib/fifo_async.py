from myhdl import *
from mem   import ram_sdp_ar


def fifo_async(wrst, rrst, wclk, rclk, wfull, we, wdata, rempty, re, rdata, depth=None, width=None):
    ''' Asynchronous FIFO

        Implements the design described in:
            Clifford E. Cummings, "Simulation and Synthesis Techniques for Asynchronous FIFO Design," SNUG 2002 (Synopsys
            Users Group Conference, San Jose, CA, 2002) User Papers, March 2002, Section TB2, 2nd paper. Also available at
            www.sunburst-design.com/papers

        Write side interface:
            wrst   - reset 
            wclk   - clock
            wfull  - full flag, immediate set on 'write', delayed clear on 'read' due to clock domain synchronization
            we     - write enable
            wdata  - write data
        Read side interface
            rrst   - reset
            cclk   - clock
            rempty - empty flag, immediate set on 'read', delayed clear on 'write' due to clock domain synchronization
            re     - read enable
            rdata  - read data
        Parameters
            depth - fifo depth. If not set, default 4 is used. Must be >=4. Must be power of 2
            width - data width. If not set, data with equals len(wdata). Can be [0,1,2,3...)
                    It is possible to instantiate a fifo with data width 0 (no data) if width=0 or width=None and wdata=None
    '''

    if (width == None):
        width = 0
        if wdata is not None:
            width = len(wdata)

    if (depth == None):
        depth = 4
    assert depth >= 4, "Fifo_async parameter 'depth' must be >= 4 , detected depth={}".format(depth)
    assert (depth & (depth-1)) == 0, "Fifo_async parameter 'depth' must be 2**n, detected depth={}".format(depth)


    full_flg        = Signal(bool(1))
    empty_flg       = Signal(bool(1))
    full_val        = Signal(bool(1))
    empty_val       = Signal(bool(1))
    we_safe         = Signal(bool(0))
    re_safe         = Signal(bool(0))
    rd_ptr          = Signal(intbv(0, min=0, max=depth))
    wr_ptr          = Signal(intbv(0, min=0, max=depth))

    WIDTH = len(rd_ptr)

    rd_ptr_bin          = Signal(intbv(0)[WIDTH+1:])
    rd_ptr_bin_new      = Signal(intbv(0)[WIDTH+1:])
    rd_ptr_gray         = Signal(intbv(0)[WIDTH+1:])
    rd_ptr_gray_new     = Signal(intbv(0)[WIDTH+1:])
    rd_ptr_gray_sync1   = Signal(intbv(0)[WIDTH+1:])
    rd_ptr_gray_sync2   = Signal(intbv(0)[WIDTH+1:])
    wr_ptr_bin          = Signal(intbv(0)[WIDTH+1:])
    wr_ptr_bin_new      = Signal(intbv(0)[WIDTH+1:])
    wr_ptr_gray         = Signal(intbv(0)[WIDTH+1:])
    wr_ptr_gray_new     = Signal(intbv(0)[WIDTH+1:])
    wr_ptr_gray_sync1   = Signal(intbv(0)[WIDTH+1:])
    wr_ptr_gray_sync2   = Signal(intbv(0)[WIDTH+1:])

    @always_comb
    def safe_read_write():
        wfull.next      = full_flg
        rempty.next     = empty_flg
        we_safe.next    = we and not full_flg
        re_safe.next    = re and not empty_flg

    @always(wclk.posedge)
    def sync_r2w():
        ''' Read-domain to write-domain synchronizer '''
        if (wrst):
            rd_ptr_gray_sync1.next = 0
            rd_ptr_gray_sync2.next = 0
        else:
            rd_ptr_gray_sync1.next = rd_ptr_gray
            rd_ptr_gray_sync2.next = rd_ptr_gray_sync1

    @always(rclk.posedge)
    def sync_w2r():
        ''' Write-domain to read-domain synchronizer '''
        if (rrst):
            wr_ptr_gray_sync1.next = 0
            wr_ptr_gray_sync2.next = 0
        else:
            wr_ptr_gray_sync1.next = wr_ptr_gray
            wr_ptr_gray_sync2.next = wr_ptr_gray_sync1

    @always_comb
    def bin_comb():
        wr_ptr_bin_new.next = wr_ptr_bin
        rd_ptr_bin_new.next = rd_ptr_bin
        if (we_safe):
            wr_ptr_bin_new.next = (wr_ptr_bin + 1) % wr_ptr_bin.max
        if (re_safe):
            rd_ptr_bin_new.next = (rd_ptr_bin + 1) % rd_ptr_bin.max

    @always_comb
    def gray_comb():
        wr_ptr_gray_new.next    = (wr_ptr_bin_new >> 1) ^ wr_ptr_bin_new
        rd_ptr_gray_new.next    = (rd_ptr_bin_new >> 1) ^ rd_ptr_bin_new

    @always_comb
    def full_empty_comb():
        empty_val.next  = (rd_ptr_gray_new == wr_ptr_gray_sync2)
        full_val.next   = (wr_ptr_gray_new[WIDTH] != rd_ptr_gray_sync2[WIDTH]) and \
                          (wr_ptr_gray_new[WIDTH-1] != rd_ptr_gray_sync2[WIDTH-1]) and \
                          (wr_ptr_gray_new[WIDTH-1:] == rd_ptr_gray_sync2[WIDTH-1:])


    @always(wclk.posedge)
    def wptr_proc():
        if (wrst):
            wr_ptr_bin.next     = 0
            wr_ptr_gray.next    = 0
            full_flg.next       = 0
        else:
            wr_ptr_bin.next     = wr_ptr_bin_new
            wr_ptr_gray.next    = wr_ptr_gray_new
            full_flg.next       = full_val

    @always(rclk.posedge)
    def rptr_proc():
        if (rrst):
            rd_ptr_bin.next     = 0
            rd_ptr_gray.next    = 0
            empty_flg.next      = 1
        else:
            rd_ptr_bin.next     = rd_ptr_bin_new
            rd_ptr_gray.next    = rd_ptr_gray_new
            empty_flg.next      = empty_val


    if width>0:
        #===========================================================================
        # Memory instance
        #===========================================================================
        mem_we      = Signal(bool(0))
        mem_addrw   = Signal(intbv(0, min=0, max=depth))
        mem_addrr   = Signal(intbv(0, min=0, max=depth))
        mem_di      = Signal(intbv(0)[width:0])
        mem_do      = Signal(intbv(0)[width:0])


        # RAM: Simple-Dual-Port, Asynchronous read
        mem = ram_sdp_ar(   clk     = wclk,
                            we      = mem_we,
                            addrw   = mem_addrw,
                            addrr   = mem_addrr,
                            di      = mem_di,
                            do      = mem_do )

        @always_comb
        def mem_connect():
            mem_we.next         = we_safe
            mem_addrw.next      = wr_ptr_bin[WIDTH:]
            mem_addrr.next      = rd_ptr_bin[WIDTH:]
            mem_di.next         = wdata
            rdata.next          = mem_do


    return instances()


def convert(depth=256, width=8):
    wrst, rrst, wclk, rclk   = [Signal(bool(0)) for _ in range(4)]
    wdata, rdata  = [Signal(intbv(0)[width:]) for _ in range(2)]
    re, we, rempty, wfull = [Signal(bool(0)) for _ in range(4)]

    toVerilog(fifo_async, wrst, rrst, wclk, rclk, wfull, we, wdata, rempty, re, rdata, depth=depth, width=width)



if __name__ == '__main__':
    convert()