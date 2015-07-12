import unittest

from myhdl import *
from myhdl_lib.mux import ls_mux
import myhdl_lib.simulation as sim

import random


class TestLsMux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def testLsMux2(self):
        ''' LS_MUX: 5 inputs'''
        DMAX = 100
        NUM_INPUTS = 5

        def ls_mux_top(sel, 
                       di_00, di_01, di_02,
                       di_10, di_11, di_12,
                       di_20, di_21, di_22,
                       di_30, di_31, di_32,
                       di_40, di_41, di_42,
                       do_0, do_1, do_2):
            ''' Needed when ls_mux is co-simulated as top level'''
            lsls_di_00 = Signal(bool(0))
            lsls_di_01 = Signal(intbv(0,min=0,max=DMAX))
            lsls_di_02 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_di_10 = Signal(bool(0))
            lsls_di_11 = Signal(intbv(0,min=0,max=DMAX))
            lsls_di_12 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_di_20 = Signal(bool(0))
            lsls_di_21 = Signal(intbv(0,min=0,max=DMAX))
            lsls_di_22 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_di_30 = Signal(bool(0))
            lsls_di_31 = Signal(intbv(0,min=0,max=DMAX))
            lsls_di_32 = Signal(intbv(0,min=-DMAX,max=DMAX))

            lsls_di_40 = Signal(bool(0))
            lsls_di_41 = Signal(intbv(0,min=0,max=DMAX))
            lsls_di_42 = Signal(intbv(0,min=-DMAX,max=DMAX))

            ls_do_0 = Signal(bool(0))
            ls_do_1 = Signal(intbv(0,min=0,max=DMAX))
            ls_do_2 = Signal(intbv(0,min=-DMAX,max=DMAX))

            @always_comb
            def _assign():
                lsls_di_00.next = di_00
                lsls_di_01.next = di_01
                lsls_di_02.next = di_02
                lsls_di_10.next = di_10
                lsls_di_11.next = di_11
                lsls_di_12.next = di_12
                lsls_di_20.next = di_20
                lsls_di_21.next = di_21
                lsls_di_22.next = di_22
                lsls_di_30.next = di_30
                lsls_di_31.next = di_31
                lsls_di_32.next = di_32
                lsls_di_40.next = di_40
                lsls_di_41.next = di_41
                lsls_di_42.next = di_42

                do_0.next = ls_do_0
                do_1.next = ls_do_1
                do_2.next = ls_do_2

            lsls_di = [[lsls_di_00, lsls_di_01, lsls_di_02],
                       [lsls_di_10, lsls_di_11, lsls_di_12],
                       [lsls_di_20, lsls_di_21, lsls_di_22],
                       [lsls_di_30, lsls_di_31, lsls_di_32],
                       [lsls_di_40, lsls_di_41, lsls_di_42]]

            ls_do = [ls_do_0, ls_do_1, ls_do_2]

            _ls_mux = ls_mux(sel=sel, lsls_di=lsls_di, ls_do=ls_do)
            return instances()


        sel = Signal(intbv(0,min=0,max=NUM_INPUTS))
        lsls_di = [[Signal(bool(0)),
                    Signal(intbv(0,min=0,max=DMAX)),
                    Signal(intbv(0,min=-DMAX,max=DMAX))] for _ in range(NUM_INPUTS)]

        ls_do = [Signal(bool(0)),
                 Signal(intbv(0,min=0,max=DMAX)),
                 Signal(intbv(0,min=-DMAX,max=DMAX))]

        argl = {"sel":sel, 
                "di_00":lsls_di[0][0], "di_01":lsls_di[0][1], "di_02":lsls_di[0][2],
                "di_10":lsls_di[1][0], "di_11":lsls_di[1][1], "di_12":lsls_di[1][2],
                "di_20":lsls_di[2][0], "di_21":lsls_di[2][1], "di_22":lsls_di[2][2],
                "di_30":lsls_di[3][0], "di_31":lsls_di[3][1], "di_32":lsls_di[3][2],
                "di_40":lsls_di[4][0], "di_41":lsls_di[4][1], "di_42":lsls_di[4][2],
                "do_0":ls_do[0],"do_1":ls_do[1],"do_2":ls_do[2]}

        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(NUM_INPUTS):
                    for j in range(3):
                        lsls_di[i][j].next = 0
                yield delay(10)

                for _ in range(2):
                    d = [[random.randint(0,1),
                          random.randint(0,DMAX-1),
                          random.randint(-DMAX,DMAX-1)] for _ in range(NUM_INPUTS)]
                    for i in range(NUM_INPUTS):
                        for j in range(3):
                            lsls_di[i][j].next = d[i][j]

                    for s in range(NUM_INPUTS):
                        sel.next = s
                        yield delay(10)
                        assert d[s][0] == ls_do[0], "Mux output (sel={}): expected {}, detected {}".format(sel, d[s], [int(x) for x in ls_do])
                        assert d[s][1] == ls_do[1], "Mux output (sel={}): expected {}, detected {}".format(sel, d[s], [int(x) for x in ls_do])
                        assert d[s][2] == ls_do[2], "Mux output (sel={}): expected {}, detected {}".format(sel, d[s], [int(x) for x in ls_do])

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(ls_mux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()