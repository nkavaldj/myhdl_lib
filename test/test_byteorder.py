import unittest

from myhdl import *
from myhdl_lib.utils import byteorder
import myhdl_lib.simulation as sim

import random


class TestByteorder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def test56bits(self):
        ''' BYTEORDER: 7*8 bits'''
        BYTES = 7
        BITS = BYTES*8

        bv_di = Signal(intbv(0)[BITS:])
        bv_do = Signal(intbv(0)[BITS:])

        argl = {"bv_di":bv_di, "bv_do":bv_do, "REVERSE":True}

        def stim():
            @instance
            def _inst():
                bv_di.next = 0
                yield delay(10)
                assert 0 == bv_do, "Byteorder (reverse={}): expected {}, detected {}".format(reverse, 0, bv_do)

                for _ in range(10):
                    bv_di.next = random.randint(0,bv_di.max-1)
                    yield delay(10)
                    if reverse:
                        for b in range(BYTES):
                            assert bv_di[(b+1)*8:b*8] == bv_do[(BYTES-b)*8:(BYTES-b-1)*8], "Byteorder byte {}: {} {}".format(b, hex(bv_di,BYTES), hex(bv_do,BYTES))
                    else:
                        for b in range(BYTES):
                            assert bv_di[(b+1)*8:b*8] == bv_do[(b+1)*8:b*8], "Byteorder byte {}: {} {}".format(b, hex(bv_di), hex(bv_do))

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for reverse in [False, True]:
                argl["REVERSE"] = reverse
                dut=getDut(byteorder, **argl)
                stm = stim()
                Simulation( dut, stm).run()
                del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()