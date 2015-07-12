import unittest

from myhdl import *
from myhdl_lib.mux import ls_demux
import myhdl_lib.simulation as sim

import random


class TestLsDemux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def testLsDemux5(self):
        ''' LS_DEMUX: 5 outputs '''
        DMAX = 100
        NUM_OUTPUTS = 5

        def ls_demux_top(sel, 
                       di_0, di_1, di_2,
                       do_00, do_01, do_02,
                       do_10, do_11, do_12,
                       do_20, do_21, do_22,
                       do_30, do_31, do_32,
                       do_40, do_41, do_42):
            ''' Needed when ls_demux is co-simulated as top level'''
            ls_di_0 = Signal(bool(0))
            ls_di_1 = Signal(intbv(0,min=0,max=DMAX))
            ls_di_2 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_do_00 = Signal(bool(0))
            lsls_do_01 = Signal(intbv(0,min=0,max=DMAX))
            lsls_do_02 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_do_10 = Signal(bool(0))
            lsls_do_11 = Signal(intbv(0,min=0,max=DMAX))
            lsls_do_12 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_do_20 = Signal(bool(0))
            lsls_do_21 = Signal(intbv(0,min=0,max=DMAX))
            lsls_do_22 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_do_30 = Signal(bool(0))
            lsls_do_31 = Signal(intbv(0,min=0,max=DMAX))
            lsls_do_32 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_do_40 = Signal(bool(0))
            lsls_do_41 = Signal(intbv(0,min=0,max=DMAX))
            lsls_do_42 = Signal(intbv(0,min=-DMAX,max=DMAX))

            @always_comb
            def _assign():
                ls_di_0.next = di_0
                ls_di_1.next = di_1
                ls_di_2.next = di_2

                do_00.next = lsls_do_00
                do_01.next = lsls_do_01
                do_02.next = lsls_do_02
                do_10.next = lsls_do_10
                do_11.next = lsls_do_11
                do_12.next = lsls_do_12
                do_20.next = lsls_do_20
                do_21.next = lsls_do_21
                do_22.next = lsls_do_22
                do_30.next = lsls_do_30
                do_31.next = lsls_do_31
                do_32.next = lsls_do_32
                do_40.next = lsls_do_40
                do_41.next = lsls_do_41
                do_42.next = lsls_do_42

            lsls_do = [[lsls_do_00, lsls_do_01, lsls_do_02],
                       [lsls_do_10, lsls_do_11, lsls_do_12],
                       [lsls_do_20, lsls_do_21, lsls_do_22],
                       [lsls_do_30, lsls_do_31, lsls_do_32],
                       [lsls_do_40, lsls_do_41, lsls_do_42]]

            ls_di = [ls_di_0, ls_di_1, ls_di_2]

            _ls_demux = ls_demux(sel=sel, ls_di=ls_di, lsls_do=lsls_do)
            return instances()


        sel = Signal(intbv(0,min=0,max=NUM_OUTPUTS))

        ls_di = [Signal(bool(0)),
                 Signal(intbv(0,min=0,max=DMAX)),
                 Signal(intbv(0,min=-DMAX,max=DMAX))]

        lsls_do = [[Signal(bool(0)),
                    Signal(intbv(0,min=0,max=DMAX)),
                    Signal(intbv(0,min=-DMAX,max=DMAX))] for _ in range(NUM_OUTPUTS)]

        argl = {"sel":sel, 
                "di_0":ls_di[0],"di_1":ls_di[1],"di_2":ls_di[2],
                "do_00":lsls_do[0][0], "do_01":lsls_do[0][1], "do_02":lsls_do[0][2],
                "do_10":lsls_do[1][0], "do_11":lsls_do[1][1], "do_12":lsls_do[1][2],
                "do_20":lsls_do[2][0], "do_21":lsls_do[2][1], "do_22":lsls_do[2][2],
                "do_30":lsls_do[3][0], "do_31":lsls_do[3][1], "do_32":lsls_do[3][2],
                "do_40":lsls_do[4][0], "do_41":lsls_do[4][1], "do_42":lsls_do[4][2]}

        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(3):
                    ls_di[i].next = 0
                yield delay(10)

                for _ in range(2):
                    d = [[random.randint(0,1),
                          random.randint(0,DMAX-1),
                          random.randint(-DMAX,DMAX-1)] for _ in range(NUM_OUTPUTS)]

                    for s in range(NUM_OUTPUTS):
                        for j in range(3):
                            ls_di[j].next = d[s][j]
                        sel.next = s
                        yield delay(10)

                        for o in range(NUM_OUTPUTS):
                            if s == o:
                                assert d[s][0] == lsls_do[o][0], "Mux output {} (sel={}): expected {}, detected {}".format(o, sel, d[s], [int(x) for x in lsls_do[o]])
                                assert d[s][1] == lsls_do[o][1], "Mux output {} (sel={}): expected {}, detected {}".format(o, sel, d[s], [int(x) for x in lsls_do[o]])
                                assert d[s][2] == lsls_do[o][2], "Mux output {} (sel={}): expected {}, detected {}".format(o, sel, d[s], [int(x) for x in lsls_do[o]])
                            else:
                                assert 0 == lsls_do[o][0], "Mux output {} (sel={}): expected {}, detected {}".format(o, sel, 3*[0], [int(x) for x in lsls_do[o]])
                                assert 0 == lsls_do[o][1], "Mux output {} (sel={}): expected {}, detected {}".format(o, sel, 3*[0], [int(x) for x in lsls_do[o]])
                                assert 0 == lsls_do[o][2], "Mux output {} (sel={}): expected {}, detected {}".format(o, sel, 3*[0], [int(x) for x in lsls_do[o]])

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(ls_demux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()