import unittest

from myhdl import *
from myhdl_lib.mux import demux
import myhdl_lib.simulation as sim

import random


class TestDemux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def testDemux5(self):
        ''' DEMUX: 5 outputs '''
        DMAX = 100
        NUM_OUTPUTS = 5

        def demux_top(sel, di, do_0, do_1, do_2, do_3, do_4):
            ''' Needed when demux is co-simulated as top level'''
            ls_do = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_OUTPUTS)]
            @always_comb
            def _assign():
                do_0.next = ls_do[0]
                do_1.next = ls_do[1]
                do_2.next = ls_do[2]
                do_3.next = ls_do[3]
                do_4.next = ls_do[4]

            inst = demux(sel=sel, di=di, ls_do=ls_do)
            return instances()

        sel = Signal(intbv(0,min=0,max=NUM_OUTPUTS))
        di = Signal(intbv(0,min=0,max=DMAX))
        ls_do = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_OUTPUTS)]

        argl = {"sel":sel, "di":di, "do_0":ls_do[0], "do_1":ls_do[1], "do_2":ls_do[2], "do_3":ls_do[3], "do_4":ls_do[4]}


        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(NUM_OUTPUTS):
                    di.next = 0
                    sel.next = 0
                yield delay(10)

                for _ in range(10):
                    d = [random.randint(0,DMAX-1) for _ in range(NUM_OUTPUTS)]

                    for s in range(NUM_OUTPUTS):
                        di.next = d[s]
                        sel.next = s
                        yield delay(10)

                        for i in range(NUM_OUTPUTS):
                            if s == i:
                                assert d[s] == ls_do[i], "Mux output {} (sel={}): expected {}, detected {}".format(i, sel, d[s], ls_do[i])
                            else:
                                assert 0 == ls_do[i], "Mux output {} (sel={}): expected {}, detected {}".format(i, sel, d[s], ls_do[i])

                yield delay(10)
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(demux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


    def testDemux2(self):
        ''' DEMUX: 2 outputs, boolean Select '''
        DMAX = 100
        NUM_OUTPUTS = 2

        def demux_top(sel, di, do_0, do_1):
            ''' Needed when demux is co-simulated as top level'''
            ls_do = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_OUTPUTS)]
            @always_comb
            def _assign():
                do_0.next = ls_do[0]
                do_1.next = ls_do[1]

            inst = demux(sel=sel, di=di, ls_do=ls_do)
            return instances()

        sel = Signal(bool(0))
        di = Signal(intbv(0,min=0,max=DMAX))
        ls_do = [Signal(intbv(0,min=0,max=DMAX)) for _ in range(NUM_OUTPUTS)]

        argl = {"sel":sel, "di":di, "do_0":ls_do[0], "do_1":ls_do[1]}


        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(NUM_OUTPUTS):
                    di.next = 0
                    sel.next = 0
                yield delay(10)

                for _ in range(10):
                    d = [random.randint(0,DMAX-1) for _ in range(NUM_OUTPUTS)]

                    for s in range(NUM_OUTPUTS):
                        di.next = d[s]
                        sel.next = s
                        yield delay(10)

                        for i in range(NUM_OUTPUTS):
                            if s == i:
                                assert d[s] == ls_do[i], "Mux output {} (sel={}): expected {}, detected {}".format(i, sel, d[s], ls_do[i])
                            else:
                                assert 0 == ls_do[i], "Mux output {} (sel={}): expected {}, detected {}".format(i, sel, 0, ls_do[i])

                yield delay(10)
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(demux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()