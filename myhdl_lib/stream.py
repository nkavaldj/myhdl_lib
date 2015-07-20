from myhdl import *

from math import log, floor, ceil
from myhdl_lib.utils import assign

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


def checksum(rst, clk, rx_vld, rx_sop, rx_eop, rx_dat, rx_mty, chksum, sum16=None, sumN=None, init_sum=None, MAX_BYTES=1500):
    """ Calculates checksum on a stream of packetised data
            rx_vld   - (i) valid data
            rx_sop   - (i) start of packet
            rx_eop   - (i) end of packet
            rx_dat   - (i) data
            rx_mty   - (i) empty bits when rx_eop
            init_sum - (i) initial value for the sum (e.g. sum of the some fields from a packet header)
            sumN     - (o) optional, plane sum
            sum16    - (o) optional, 16 bit sum (every time the sum overflows, the overflow is added to the sum)
            chksum   - (o) optional, checksum (~sum16)
            MAX_BYTES - a limit: maximum number of bytes that may arrive in a single packet
        Assumes Big-endian data.
        The results are ready in the first clock cycle after rx_eop
    """

    DATA_WIDTH = len(rx_dat) 

    assert DATA_WIDTH%16==0, "checksum: expects len(rx_dat)=16*x, but len(tx_dat)={}".format(DATA_WIDTH)

    NUM_BYTES = DATA_WIDTH // 8
    NUM_WORDS = DATA_WIDTH // 16

    SUM_WIDTH    = 16 + int(ceil(log(MAX_BYTES/2,2))) + 1
    SUM16_WIDTH  = 16 + int(ceil(log(NUM_WORDS,2))) + 1


    if (init_sum != None):
        assert len(init_sum)<=16, "checksum: expects len(init_sum)<={}, but len(init_sum)={}".format(16, len(init_sum))
        SUM_WIDTH    += 1
        SUM16_WIDTH  += 1
    else:
        init_sum = 0

    FF_MASK = intbv(0)[DATA_WIDTH:].max-1
    mdata = Signal(intbv(0)[DATA_WIDTH:])

    @always_comb
    def _mask_empty():
        mdata.next = rx_dat
        if rx_eop:
            mdata.next = rx_dat & (FF_MASK<<(rx_mty*8))

    # Slice masked data in 16 bit words
    mdata16 = [Signal(intbv(0)[16:]) for _ in range(NUM_WORDS)]
    _ass = [assign(mdata16[w], mdata((w+1)*16, w*16)) for w in range(NUM_WORDS)]

    if sumN!=None:
        assert len(sumN)>=SUM_WIDTH, "checksum: expects len(sumN)>={}, but len(sumN)={}".format(SUM_WIDTH, len(sumN))

        sumN_reg = Signal(intbv(0)[SUM_WIDTH:])

        @always_seq(clk.posedge, reset=rst)
        def _accuN():
            ''' Accumulate '''
            if (rx_vld):
                s = 0

                if (rx_sop):
                    s = int(init_sum)
                else:
                    s = int(sumN_reg)

                for w in range(NUM_WORDS):
                    s += mdata16[w]

                sumN_reg.next = s

        @always_comb
        def _passN():
            sumN.next = sumN_reg


    if chksum!=None or sum16!=None:

        sum16_reg = Signal(intbv(0)[SUM16_WIDTH:])

        @always_seq(clk.posedge, reset=rst)
        def _accu16():
            ''' Accumulate 16 bit words'''
            if (rx_vld):
                s = 0

                if (rx_sop):
                    s = int(init_sum)
                else:
                    s = int(sum16_reg)

                for w in range(NUM_WORDS):
                    s += mdata16[w]

                ss = intbv(s)[SUM16_WIDTH:]

                sum16_reg.next = ss[:2*8] + ss[2*8:]

        if sum16!=None:
            assert len(sum16)>=16, "checksum: expects len(sum16)>={}, but len(sum16)={}".format(16, len(sum16))
            @always_comb
            def _pass16():
                sum16.next = sum16_reg[16:]

        if chksum!=None:
            assert len(chksum)>=16, "checksum: expects len(chksum)>={}, but len(chksum)={}".format(16, len(chksum))
            @always_comb
            def _invert():
                chksum.next = ~sum16_reg[16:] & 0xFFFF

    return instances()



if __name__ == '__main__':
    pass

