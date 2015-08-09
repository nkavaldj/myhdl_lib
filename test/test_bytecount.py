import unittest

from myhdl import *
from myhdl_lib.stream import bytecount
import myhdl_lib.simulation as sim

import random
from math import log, floor, ceil


class TestBytecount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def testName(self):
        ''' BYTECOUNT: '''
        MAX_NUM_BYTES = 200
        BYTES_PER_WORD = [1,2,3,4,5]

        getDut = sim.DUTer()

        def testbench(BYTES_PER_WORD):
            MTY_WIDTH = int(floor(log(BYTES_PER_WORD,2))) + 1
            COUNT_WIDTH = int(floor(log(MAX_NUM_BYTES,2))) + 1

            clk = sim.Clock(val=0, period=10, units="ns")
            rst = sim.ResetSync(clk=clk, val=0, active=1)

            rx_vld = Signal(bool(0))
            rx_sop = Signal(bool(0))
            rx_eop = Signal(bool(0))
            rx_dat = Signal(intbv(0)[BYTES_PER_WORD*8:])
            rx_mty = Signal(intbv(0)[MTY_WIDTH:])
            count = Signal(intbv(0)[COUNT_WIDTH:])

            argl = {"rst":rst,
                    "clk":clk,
                    "rx_vld":rx_vld,
                    "rx_sop":rx_sop,
                    "rx_eop":rx_eop,
                    "rx_dat":rx_dat,
                    "rx_mty":rx_mty,
                    "count":count,
                    "MAX_BYTES":MAX_NUM_BYTES}

            dut = getDut(bytecount, **argl)
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
                assert 0==count, "bytecount: expected {}, detected {}".format(0, count)

                for _ in range(10):
                    bytes = random.randint(1,MAX_NUM_BYTES)
                    words = int(ceil(float(bytes)/BYTES_PER_WORD))
                    empty_n = bytes%BYTES_PER_WORD
                    empty = BYTES_PER_WORD - empty_n
                    C = 0
                    for i in range(words):
                        rx_vld.next = 1
                        rx_sop.next = (i==0)
                        rx_eop.next = (i==words-1)
                        rx_dat.next = random.randint(0,2**BYTES_PER_WORD*8-1)
                        rx_mty.next = empty if i==words-1 else 0
                        C = C + (empty_n if i==words-1 else BYTES_PER_WORD)
                        yield clk.posedge
                        yield delay(1)
                        assert C==count, "bytecount: expected {}, detected {}".format(C, count)
                        # Gap
                        rx_vld.next = 0
                        for _ in range(random.randint(0,3)):
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
