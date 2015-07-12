import unittest

from myhdl import *
from myhdl_lib.mux import mux
import myhdl_lib.simulation as sim

import random




class TestMux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def testMux5(self):
        """ MUX: 5 inputs"""
        DMAX = 100
        NUM_INPUTS = 5

        def mux_top(sel, di_0, di_1, di_2, di_3, di_4, do):
            ''' Needed when mux is co-simulated as top level'''
            ls_di = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_INPUTS)]
            @always_comb
            def _assign():
                ls_di[0].next = di_0
                ls_di[1].next = di_1
                ls_di[2].next = di_2
                ls_di[3].next = di_3
                ls_di[4].next = di_4

            inst = mux(sel=sel, ls_di=ls_di, do=do)
            return instances()

        sel = Signal(intbv(0,min=0,max=NUM_INPUTS))
        ls_di = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_INPUTS)]
        do = Signal(intbv(0,min=0,max=DMAX))

        argl = {"sel":sel, "di_0":ls_di[0], "di_1":ls_di[1], "di_2":ls_di[2], "di_3":ls_di[3], "di_4":ls_di[4], "do":do}

        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(NUM_INPUTS):
                    ls_di[i].next = 0
                yield delay(10)

                for _ in range(10):
                    d = [random.randint(0,DMAX-1) for _ in range(NUM_INPUTS)]
                    for i in range(NUM_INPUTS):
                        ls_di[i].next = d[i]

                    for s in range(NUM_INPUTS):
                        sel.next = s
                        yield delay(10)
                        assert d[s] == do, "Mux output (sel={}): expected {}, detected {}".format(sel, d[s], do)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(mux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


    def testMux2(self):
        """ MUX: 2 inputs, boolean Select"""
        DMAX = 100
        NUM_INPUTS = 2

        def mux_top(sel, di_0, di_1, do):
            ''' Needed when mux is co-simulated as top level'''
            ls_di = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_INPUTS)]
            @always_comb
            def _assign():
                ls_di[0].next = di_0
                ls_di[1].next = di_1

            inst = mux(sel=sel, ls_di=ls_di, do=do)
            return instances()

        sel = Signal(bool(0))
        ls_di = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_INPUTS)]
        do = Signal(intbv(0,min=0,max=DMAX))

        argl = {"sel":sel, "di_0":ls_di[0], "di_1":ls_di[1], "do":do}

        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(NUM_INPUTS):
                    ls_di[i].next = 0
                yield delay(10)

                for _ in range(10):
                    d = [random.randint(0,DMAX-1) for _ in range(NUM_INPUTS)]
                    for i in range(NUM_INPUTS):
                        ls_di[i].next = d[i]

                    for s in range(NUM_INPUTS):
                        sel.next = s
                        yield delay(10)
                        assert d[s] == do, "Mux output (sel={}): expected {}, detected {}".format(sel, d[s], do)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(mux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testMux']
    unittest.main()
