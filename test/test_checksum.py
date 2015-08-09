import unittest

from myhdl import *
from myhdl_lib.stream import checksum
import myhdl_lib.simulation as sim

import random
from math import log, ceil


class TestChecksum(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def testRand(self):
        ''' CHECKSUM: Random '''
        MAX_NUM_BYTES = 200
        BYTES_PER_WORD = [2,4,6,8]
        getDut = sim.DUTer()

        def testbench(BYTES_PER_WORD):
            W16_PER_WORD = BYTES_PER_WORD//2
            SUM_WIDTH = 16 + int(ceil(log(MAX_NUM_BYTES/2,2))) + 1

            clk = sim.Clock(val=0, period=10, units="ns")
            rst = sim.ResetSync(clk=clk, val=0, active=1)

            rx_vld = Signal(bool(0))
            rx_sop = Signal(bool(0))
            rx_eop = Signal(bool(0))
            rx_dat = Signal(intbv(0)[BYTES_PER_WORD*8:])
            rx_mty = Signal(intbv(0, min=0, max=BYTES_PER_WORD))
            sumN = Signal(intbv(0)[SUM_WIDTH:])
            sum16 = Signal(intbv(0)[16:])
            sum16n = Signal(intbv(0)[16:])

            argl = {"rst":rst,
                    "clk":clk,
                    "rx_vld":rx_vld,
                    "rx_sop":rx_sop,
                    "rx_eop":rx_eop,
                    "rx_dat":rx_dat,
                    "rx_mty":rx_mty,
                    "chksum":sum16n,
                    "sum16":sum16,
                    "sumN":sumN,
                    "MAX_BYTES":MAX_NUM_BYTES}

            dut = getDut(checksum, **argl)
            clkgen = clk.gen()

            @instance
            def _stim():
                rx_vld.next = 0
                rx_sop.next = 0
                rx_eop.next = 0
                rx_dat.next = 0
                rx_mty.next = 0
                yield rst.pulse(10)
                yield clk.posedge
                S = intbv(0)[SUM_WIDTH:]
                S16 = S[16:] + S[:16]
                S16n = ~S16 & 0xFFFF
                assert S16n==sum16n, "checksum sum16n: expected {}, detected {}".format(hex(S16n), hex(sum16n))
                assert S16==sum16, "checksum sum16: expected {}, detected {}".format(hex(S16), hex(sum16))
                assert S==sumN, "checksum sumN: expected {}, detected {}".format(hex(S), hex(sumN))

                for _ in range(10):
                    bytes = random.randint(1,MAX_NUM_BYTES)
                    words = int(ceil(float(bytes)/BYTES_PER_WORD))
                    empty = (BYTES_PER_WORD - bytes%BYTES_PER_WORD)%BYTES_PER_WORD
                    S = intbv(0)[SUM_WIDTH:]
                    S16 = S[16:] + S[:16]
                    S16n = ~S16 & 0xFFFF
                    for i in range(words):
                        rx_vld.next = 1
                        rx_sop.next = (i==0)
                        rx_eop.next = (i==words-1)
                        rx_dat.next = random.randint(0,(2**(BYTES_PER_WORD*8))-1)
                        rx_mty.next = empty if i==words-1 else 0
                        d = rx_dat.next
                        if rx_eop.next:
                            d[:] = d & ((intbv(0)[BYTES_PER_WORD*8:].max-1)<<(8*rx_mty.next))
                        # Sum the word
                        for i in range(W16_PER_WORD):
                            S[:] = S[:] + d[16*(i+1):16*i]
                        # Resuce sum to 16 bit
                        S16 = S[:]
                        while S16>S16[16:]:
                            S16[:] = S16[16:] + S16[:16]
                        S16[:] = S16[16:]
                        # Invert
                        S16n = ~S16 & 0xFFFF

                        yield clk.posedge
                        yield delay(1)
                        assert S16n==sum16n, "checksum sum16n: expected {}, detected {}".format(hex(S16n), hex(sum16n))
                        assert S16==sum16, "checksum sum16: expected {}, detected {}".format(hex(S16), hex(sum16))
                        assert S==sumN, "checksum sumN: expected {}, detected {}".format(hex(S), hex(sumN))
                        # Gap
                        rx_vld.next = 0
                        for _ in range(random.randint(0,1)):
                            yield clk.posedge

                yield clk.posedge
                raise StopSimulation
            return instances()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for BPW in BYTES_PER_WORD:
                tb = testbench(BPW)
                Simulation(tb).run()
                del tb


    def testOverflow(self):
        ''' CHECKSUM: Overflow '''
        MAX_NUM_BYTES = 201
        BYTES_PER_WORD = [2,4,6,8]
        getDut = sim.DUTer()

        def testbench(BYTES_PER_WORD):
            W16_PER_WORD = BYTES_PER_WORD//2
            SUM_WIDTH = 16 + int(ceil(log(MAX_NUM_BYTES/2,2))) + 1
            INIT_WIDTH = 16
            SUM_WIDTH += 1

            clk = sim.Clock(val=0, period=10, units="ns")
            rst = sim.ResetSync(clk=clk, val=0, active=1)

            rx_vld = Signal(bool(0))
            rx_sop = Signal(bool(0))
            rx_eop = Signal(bool(0))
            rx_dat = Signal(intbv(0)[BYTES_PER_WORD*8:])
            rx_mty = Signal(intbv(0, min=0, max=BYTES_PER_WORD))
            init_sum = Signal(intbv(0)[INIT_WIDTH:])
            sumN = Signal(intbv(0)[SUM_WIDTH:])
            sum16 = Signal(intbv(0)[16:])
            sum16n = Signal(intbv(0)[16:])

            argl = {"rst":rst,
                    "clk":clk,
                    "rx_vld":rx_vld,
                    "rx_sop":rx_sop,
                    "rx_eop":rx_eop,
                    "rx_dat":rx_dat,
                    "rx_mty":rx_mty,
                    "init_sum":init_sum,
                    "chksum":sum16n,
                    "sum16":sum16,
                    "sumN":sumN,
                    "MAX_BYTES":MAX_NUM_BYTES}

            dut = getDut(checksum, **argl)
            clkgen = clk.gen()

            @instance
            def _stim():
                rx_vld.next = 0
                rx_sop.next = 0
                rx_eop.next = 0
                rx_dat.next = 0
                rx_mty.next = 0
                yield rst.pulse(10)
                yield clk.posedge
                S = intbv(0)[SUM_WIDTH:]
                S16 = S[16:] + S[:16]
                S16n = ~S16 & 0xFFFF
                assert S16n==sum16n, "checksum sum16n: expected {}, detected {}".format(hex(S16n), hex(sum16n))
                assert S16==sum16, "checksum sum16: expected {}, detected {}".format(hex(S16), hex(sum16))
                assert S==sumN, "checksum sumN: expected {}, detected {}".format(hex(S), hex(sumN))

                for k in range(10):
                    bytes = MAX_NUM_BYTES
                    words = int(ceil(float(bytes)/BYTES_PER_WORD))
                    empty = (BYTES_PER_WORD - bytes%BYTES_PER_WORD)%BYTES_PER_WORD
                    init_sum.next = init_sum.max-1-k
                    S = intbv(init_sum.next)[SUM_WIDTH:]
                    S16 = S[16:] + S[:16]
                    S16n = ~S16 & 0xFFFF
                    for i in range(words):
                        rx_vld.next = 1
                        rx_sop.next = (i==0)
                        rx_eop.next = (i==words-1)
                        rx_dat.next = rx_dat.max-1-k
                        rx_mty.next = empty if i==words-1 else 0
                        d = rx_dat.next
                        if rx_eop.next:
                            d = rx_dat.next & ((intbv(0)[BYTES_PER_WORD*8:].max-1)<<(8*rx_mty.next))
                        # Sum the word
                        for i in range(W16_PER_WORD):
                            S[:] = S[:] + d[16*(i+1):16*i]
                        # Resuce sum to 16 bit
                        S16 = S[:]
                        while S16>S16[16:]:
                            S16[:] = S16[16:] + S16[:16]
                        S16[:] = S16[16:]
                        # Invert
                        S16n = ~S16 & 0xFFFF

                        yield clk.posedge
                        yield delay(1)
                        assert S16n==sum16n, "checksum sum16n: expected {}, detected {}".format(hex(S16n), hex(sum16n))
                        assert S16==sum16, "checksum sum16: expected {}, detected {}".format(hex(S16), hex(sum16))
                        assert S==sumN, "checksum sumN: expected {}, detected {}".format(hex(S), hex(sumN))

                        init_sum.next = 0
                        # Gap
                        rx_vld.next = 0
                        for _ in range(random.randint(0,1)):
                            yield clk.posedge

                yield clk.posedge
                raise StopSimulation
            return instances()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for BPW in BYTES_PER_WORD:
                tb = testbench(BPW)
                Simulation(tb).run()
                del tb

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()