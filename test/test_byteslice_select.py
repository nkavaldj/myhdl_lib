import unittest

from myhdl import *
from myhdl_lib.mux import byteslice_select
import myhdl_lib.simulation as sim

import random


class TestBytesliceSelect(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def test56to24(self):
        ''' BYTESLICE_SELECT: 7*8 bit -> 3*8 bit'''
        LEN_I = 7*8
        LEN_O = 3*8
        MAX_OFFSET = (LEN_I - LEN_O)//8

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
                assert 0 == bv_do, "Byteslice_select (offset={}): expected {}, detected {}".format(offset, 0, bv_do)

                for _ in range(10):
                    bv_di.next = random.randint(0, bv_di.max)
                    for i in range(MAX_OFFSET+1+1):
                        offset.next = i
                        yield delay(10)
                        exp_out = bv_di[i*8+LEN_O:i*8]
                        if i<=MAX_OFFSET:
                            assert exp_out == bv_do, "Byteslice_select (offset={}): expected {}, detected {}".format(offset, exp_out, bv_do)
                        else:
                            assert 0 == bv_do, "Byteslice_select (offset={}): expected {}, detected {}".format(offset, 0, bv_do)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(byteslice_select, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()