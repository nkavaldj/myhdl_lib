from myhdl import *

from math import log, floor

def bytecount(rst, clk, rx_vld, rx_sop, rx_eop, rx_dat, rx_mty, count, MAX_BYTES=1500 ):
    """ Counts bytes in a stream of packetised data
            rx_vld - (i) valid data
            rx_sop - (i) start of packet
            rx_eop - (i) end of packet
            rx_dat - (i) data
            rx_mty - (i) empty bits when rx_eop
            count  - (o) byte count
            MAX_BYTES - a limit: maximum number of bytes that may arrive in a single packet
        The result is ready in the first clock cycle after rx_eop
    """

    DATA_WIDTH    = len(rx_dat) 

    assert DATA_WIDTH%8==0, "bytecount: expects len(rx_dat)=8*x, but len(rx_dat)={}".format(DATA_WIDTH)

    NUM_BYTES       = DATA_WIDTH // 8
    MAX_BYTES_LG    = floor(log(MAX_BYTES,2))
    MIN_COUNT_WIDTH = int(MAX_BYTES_LG) + 1

    assert len(count)>=MIN_COUNT_WIDTH, "bytecount: expects len(count)>={}, but len(count)={}".format(MIN_COUNT_WIDTH, len(count))

    count_s = Signal(intbv(0)[MIN_COUNT_WIDTH:])

    @always_seq(clk.posedge, reset=rst)
    def _count():
        if (rx_vld):
            x = NUM_BYTES
            if (rx_eop==1):
                x = x -rx_mty
            if (rx_sop==1):
                count_s.next = x
            else:
                count_s.next = count_s + x

    @always_comb
    def out_comb():
        count.next = count_s

    return instances()


if __name__ == '__main__':
    pass

