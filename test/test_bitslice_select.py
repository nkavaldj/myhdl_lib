import unittest

from myhdl import *
from myhdl_lib.mux import bitslice_select
import myhdl_lib.simulation as sim

import random


class TestBitsliceSelect(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def test20to7(self):
        ''' BITSLICE_SELECT: 20 bit -> 7 bit '''
        LEN_I = 20
        LEN_O = 7
        MAX_OFFSET = LEN_I - LEN_O

        bv_di = Signal(intbv(0)[LEN_I:])
        bv_do = Signal(intbv(0)[LEN_O:])
        offset = Signal(intbv(0, min=0, max=MAX_OFFSET+1+1))

        argl = {"offset":offset, "bv_di":bv_di, "bv_do":bv_do}

        def stim():
            @instance
            def _inst():
                offset.next = 0
                bv_di.next = 0
                yield delay(10)
                assert 0 == bv_do, "Bitslice_select (offset={}): expected {}, detected {}".format(offset, 0, bv_do)

                for _ in range(10):
                    bv_di.next = random.randint(0, bv_di.max)
                    for i in range(MAX_OFFSET+1+1):
                        offset.next = i
                        yield delay(10)
                        exp_out = bv_di[i+LEN_O:i]
                        if i<=MAX_OFFSET:
                            assert exp_out == bv_do, "Bitslice_select (offset={}): expected {}, detected {}".format(offset, exp_out, bv_do)
                        else:
                            assert 0 == bv_do, "Bitslice_select (offset={}): expected {}, detected {}".format(offset, 0, bv_do)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(bitslice_select, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()